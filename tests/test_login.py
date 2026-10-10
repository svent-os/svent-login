import ast, importlib.machinery, importlib.util, tempfile, unittest
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent

def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace('-', '_'), str(ROOT / 'bin' / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

class LoginTests(unittest.TestCase):
    def test_configuration_restore_and_preservation(self):
        module = load('configure-login')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            conf = root / 'etc/lxdm/lxdm.conf'
            conf.parent.mkdir(parents=True)
            original = '[base]\nautologin=personal\nnumlock=1\n[display]\ntheme=Industrial\n'
            conf.write_text(original)
            dm = root / 'etc/X11/default-display-manager'
            dm.parent.mkdir(parents=True)
            dm.write_text('/usr/sbin/lightdm\n')
            source = root / 'usr/share/svent/lxdm/lxdm.conf'
            source.parent.mkdir(parents=True)
            source.write_text((ROOT / 'lxdm/lxdm.conf').read_text())
            module.configure(root)
            self.assertIn('autologin = personal', conf.read_text())
            self.assertIn('theme = svent', conf.read_text())
            module.configure(root)
            module.configure(root, True)
            self.assertEqual(conf.read_text(), original)
            self.assertEqual(dm.read_text(), '/usr/sbin/lightdm\n')
            module.configure(root)
            conf.write_text('[base]\ncustom=keep\n')
            module.configure(root, True)
            self.assertIn('custom=keep', conf.read_text())

    def test_background_and_interfaces(self):
        with Image.open(ROOT / 'exports/login-background.png') as image:
            self.assertEqual(image.size, (5120,2880))
            self.assertEqual(image.format, 'PNG')
        for name in ('greeter.ui','greeter-gtk3.ui'):
            tree = ET.parse(ROOT / 'themes/svent' / name)
            objects = {node.get('id'): node for node in tree.iter('object')}
            for identifier in ('lxdm','prompt','login_entry','sessions','lang','keyboard','time','exit','user_list'):
                self.assertIn(identifier, objects)
            self.assertEqual(objects['alignment1'].find("property[@name='yscale']").text, '0')
        self.assertNotIn('GtkComboBoxEntry', (ROOT/'themes/svent/greeter-gtk3.ui').read_text())

    def test_missing_background_is_rejected(self):
        module = load('gen-background')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(FileNotFoundError):
                module.stage(root/'missing.png',root/'background.png')

if __name__ == '__main__':
    unittest.main()
