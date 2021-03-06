# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'client')
sys.path.insert(0, '../../client')
sys.path.insert(0, '.')
sys.path.insert(0, '../')
import os
import unittest
import shutil

from entropy.cache import EntropyCacher
from entropy.const import etpConst, const_mkdtemp
from entropy.output import set_mute
from entropy.client.interfaces import Client
from entropy.security import Repository, System
import entropy.tools
import tests._misc as _misc

class SecurityTest(unittest.TestCase):

    def setUp(self):
        """
        NOTE: this requires gnupg as test-dependency.
        """
        self._tmp_dir = const_mkdtemp()
        self._entropy = Client(installed_repo = False)
        self._repository = Repository(keystore_dir = self._tmp_dir)

        tmp_dir = os.getenv("TMPDIR", os.getcwd())
        self._security_cache_dir = const_mkdtemp(
            dir=tmp_dir, prefix="entropy.SecurityTest")
        self._security_dir = const_mkdtemp(
            dir=tmp_dir, prefix="entropy.SecurityTest")

        self._system = System(
            self._entropy, security_dir=self._security_dir,
            url="file://" + _misc.get_security_pkg())
        self._system._cache_dir = self._security_cache_dir

    def tearDown(self):
        """
        tearDown is run after each test
        """
        # calling destroy() and shutdown()
        # need to call destroy() directly to remove all the SystemSettings
        # plugins because shutdown() doesn't, since it's meant to be called
        # right before terminating the process
        self._entropy.destroy()
        self._entropy.shutdown()
        del self._entropy
        del self._repository
        del self._system
        shutil.rmtree(self._tmp_dir, True)
        shutil.rmtree(self._security_dir, True)
        shutil.rmtree(self._security_cache_dir, True)

    def test_security_cache(self):

        cacher = self._entropy._cacher
        # this starts the cacher as well

        cache_key = "zomg"
        data = {"1": 1, "2": 2}

        self.assertEqual(self._system._get_cache(cache_key), None)

        self._system._set_cache(cache_key, data)

        cacher.sync()

        self.assertEqual(self._system._get_cache(cache_key), data)
        self._system._set_cache(cache_key, {})

        cacher.sync()

        self.assertEqual(self._system._get_cache(cache_key), {})

    def test_security_get_empty_advisories(self):
        meta = self._system.advisories()
        self.assertEqual(meta, {})

    def test_security_fetch_advisories(self):
        set_mute(True)
        s_rc = self._system.update()
        set_mute(False)
        self.assertEqual(s_rc, 0)
        self.assertEqual(self._system.available(), True)

    def test_gpg_handling(self):

        # available keys should be empty
        self.assertEqual(self._repository.get_keys(), {})

        # now fill
        self._repository.create_keypair("foo.org", name_email = "foo@foo.org",
            expiration_days = 10)

        self.assertEqual(self._repository.is_keypair_available("foo.org"),
            True)

        # key created ?
        self.assertNotEqual(self._repository.get_keys(), {})
        self.assertTrue(self._repository.is_pubkey_available("foo.org"))

        # sign file
        rand_file = _misc.get_random_file()
        asc_file = rand_file + ".asc"
        self._repository.sign_file("foo.org", rand_file)
        self.assertEqual(
            self._repository.verify_file("foo.org", rand_file, asc_file)[0],
            True)

        # try to verify against wrong file
        wrong_rand_file = _misc.get_random_file_md5()
        self.assertEqual(
            self._repository.verify_file("foo.org", wrong_rand_file, asc_file)[0],
            False)

        # now craft signature
        with open(asc_file, "w") as asc_f:
            asc_f.write("0")
            asc_f.flush()

        self.assertEqual(
            self._repository.verify_file("foo.org", rand_file, asc_file)[0],
            False)

        os.remove(asc_file)


if __name__ == '__main__':
    unittest.main()
    raise SystemExit(0)
