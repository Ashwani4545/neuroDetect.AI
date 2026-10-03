"""
Test coverage for what's actually deterministic and testable right now:
access control on the API layer, and the modality-routing decision logic.

Deliberately NOT covered here: the ML analyzers themselves (chest_xray.py,
ecg.py, etc.) or the brain-CT inference pipeline — those need real sample
images/DICOMs to test meaningfully and are a separate follow-up, not
fabricated here just to inflate a coverage number.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import PatientScan, TelehealthConsultation


class ApiAccessControlTests(TestCase):
    """
    Regression tests for the access-control fixes: every API endpoint must
    (a) require authentication, and (b) scope reads/writes to the requesting
    user's own data. These two properties were both missing before that fix
    — this suite exists so they can't silently regress.
    """

    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pw12345!')
        self.bob = User.objects.create_user('bob', password='pw12345!')
        self.alice_scan = PatientScan.objects.create(
            user=self.alice, scan_name='alice_scan.jpg', modality='CT',
            confidence=80.0, detected=True,
        )
        self.alice_consult = TelehealthConsultation.objects.create(
            scan=self.alice_scan, assigned_doctor='Dr. Test', status='REQUESTED',
        )

    def _client_as(self, user):
        c = Client()
        c.force_login(user)
        return c

    # ── Authentication required ──────────────────────────────────────────
    def test_predict_api_requires_login(self):
        resp = Client().post(reverse('predict_api'))
        self.assertEqual(resp.status_code, 401)

    def test_patient_history_api_requires_login(self):
        resp = Client().get(reverse('patient_history'))
        self.assertEqual(resp.status_code, 401)

    def test_delete_scan_api_requires_login(self):
        resp = Client().post(reverse('delete_scan', args=[self.alice_scan.id]))
        self.assertEqual(resp.status_code, 401)

    def test_chat_api_requires_login(self):
        resp = Client().post(reverse('chat_api', args=[self.alice_scan.id]))
        self.assertEqual(resp.status_code, 401)

    def test_consult_messages_api_requires_login(self):
        resp = Client().get(reverse('consult_messages', args=[self.alice_consult.id]))
        self.assertEqual(resp.status_code, 401)

    # ── Ownership enforced (cross-user access must fail) ────────────────
    def test_patient_history_api_only_returns_own_scans(self):
        resp = self._client_as(self.bob).get(reverse('patient_history'))
        data = json.loads(resp.content)
        self.assertNotIn('alice_scan.jpg', json.dumps(data))

    def test_bob_cannot_delete_alices_scan(self):
        resp = self._client_as(self.bob).post(
            reverse('delete_scan', args=[self.alice_scan.id])
        )
        data = json.loads(resp.content)
        self.assertFalse(data.get('success'))
        self.assertTrue(PatientScan.objects.filter(id=self.alice_scan.id).exists())

    def test_bob_cannot_read_alices_consult(self):
        resp = self._client_as(self.bob).get(
            reverse('consult_messages', args=[self.alice_consult.id])
        )
        data = json.loads(resp.content)
        self.assertFalse(data.get('success'))

    def test_alice_can_delete_her_own_scan(self):
        resp = self._client_as(self.alice).post(
            reverse('delete_scan', args=[self.alice_scan.id])
        )
        data = json.loads(resp.content)
        self.assertTrue(data.get('success'))
        self.assertFalse(PatientScan.objects.filter(id=self.alice_scan.id).exists())


class ModalityRoutingTests(TestCase):
    """
    Tests the routing decision logic in core_ml/ingestion.py in isolation,
    stubbing out the actual (heavy) analyzer modules so this runs fast and
    without GPU/model dependencies.
    """

    def setUp(self):
        import tempfile, types, sys
        self.tmpdir = tempfile.mkdtemp()

        fake_result = {'confidence': '0%', 'detected': False}
        stub_targets = {
            'core_ml.inference_service': 'get_inference_service',
            'core_ml.chest_xray': 'get_chest_xray_analyzer',
            'core_ml.ecg': 'get_ecg_analyzer',
            'core_ml.blood_test': 'get_blood_test_analyzer',
            'core_ml.skin_analyzer': 'get_skin_analyzer',
            'core_ml.retinal_analyzer': 'get_retinal_analyzer',
            'core_ml.bone_xray_analyzer': 'get_bone_xray_analyzer',
            'core_ml.mri_classifier_analyzer': 'get_mri_classifier_analyzer',
        }
        self._orig_modules = {}
        for modname, fname in stub_targets.items():
            self._orig_modules[modname] = sys.modules.get(modname)
            mod = types.ModuleType(modname)
            setattr(mod, fname, lambda: types.SimpleNamespace(
                process_image=lambda p, o: dict(fake_result),
                process_pdf=lambda p: dict(fake_result),
            ))
            sys.modules[modname] = mod

    def tearDown(self):
        import sys
        for modname, orig in self._orig_modules.items():
            if orig is None:
                sys.modules.pop(modname, None)
            else:
                sys.modules[modname] = orig

    def _write(self, name, content=b'\x00'):
        import os
        path = os.path.join(self.tmpdir, name)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def test_mri_filename_is_routed_to_mri_classifier_not_ct_model(self):
        # MRI now has its own pipeline (core_ml/mri_classifier_analyzer.py) —
        # it must NOT be silently routed to the brain-CT model.
        from core_ml.ingestion import IngestionService
        path = self._write('brain_mri_scan.jpg')
        result = IngestionService().route_file(path, self.tmpdir)
        self.assertEqual(result['modality'], 'MRI')
        self.assertEqual(result['modality_confidence'], 'confirmed')

    def test_unrecognized_filename_flagged_as_default_fallback(self):
        from core_ml.ingestion import IngestionService
        path = self._write('IMG_20240101.jpg')
        result = IngestionService().route_file(path, self.tmpdir)
        self.assertEqual(result['modality'], 'CT')
        self.assertEqual(result['modality_confidence'], 'default_fallback')
        self.assertIsNotNone(result['modality_warning'])

    def test_keyword_match_is_confirmed_with_no_warning(self):
        from core_ml.ingestion import IngestionService
        path = self._write('chest_xray_001.jpg')
        result = IngestionService().route_file(path, self.tmpdir)
        self.assertEqual(result['modality'], 'CXR')
        self.assertEqual(result['modality_confidence'], 'confirmed')
        self.assertIsNone(result['modality_warning'])
