#!/usr/bin/env python3
from itertools import chain
import os
from openpilot.common.basedir import BASEDIR
from openpilot.system.ui.lib.multilang import SYSTEM_UI_DIR, UI_DIR, TRANSLATIONS_DIR, multilang

UI_DIR = os.path.join(BASEDIR, "selfdrive", "ui")
FROGPILOT_UI_DIR = os.path.join(BASEDIR, "frogpilot", "ui")
TRANSLATIONS_DIR = os.path.join(UI_DIR, "translations")
LANGUAGES_FILE = os.path.join(TRANSLATIONS_DIR, "languages.json")
TRANSLATIONS_INCLUDE_FILE = os.path.join(TRANSLATIONS_DIR, "alerts_generated.h")
PLURAL_ONLY = ["main_en"]  # base language, only create entries for strings with plural forms


def update_translations():
  files = []
  for root, _, filenames in chain(os.walk(SYSTEM_UI_DIR),
                                  os.walk(os.path.join(UI_DIR, "widgets")),
                                  os.walk(os.path.join(UI_DIR, "layouts")),
                                  os.walk(os.path.join(UI_DIR, "onroad"))):
    for filename in filenames:
      if filename.endswith(".py"):
        files.append(os.path.relpath(os.path.join(root, filename), BASEDIR))

  # Create main translation file
  cmd = ("xgettext -L Python --keyword=tr --keyword=trn:1,2 --keyword=tr_noop --from-code=UTF-8 " +
         "--flag=tr:1:python-brace-format --flag=trn:1:python-brace-format --flag=trn:2:python-brace-format " +
         f"-D {BASEDIR} -o {POT_FILE} {' '.join(files)}")

  ret = os.system(cmd)
  assert ret == 0

def update_translations(vanish: bool = False, translation_files: None | list[str] = None, translations_dir: str = TRANSLATIONS_DIR):
  if translation_files is None:
    with open(LANGUAGES_FILE) as f:
      translation_files = json.load(f).values()

  for file in translation_files:
    tr_file = os.path.join(translations_dir, f"{file}.ts")
    args = f"lupdate -locations none -recursive {UI_DIR} {FROGPILOT_UI_DIR} -ts {tr_file} -I {BASEDIR}"
    if vanish:
      args += " -no-obsolete"
    if file in PLURAL_ONLY:
      args += " -pluralonly"
    ret = os.system(args)
    assert ret == 0


if __name__ == "__main__":
  update_translations()
