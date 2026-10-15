import re
import sys
from pathlib import Path

PATH = Path("TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java")
src = PATH.read_text(encoding="utf-8")

if "badgeRow" in src:
    print("ProfileActivity уже пропатчен")
    sys.exit(0)


def edit(name, pattern, make, expected=1):
    global src
    found = len(re.findall(pattern, src, flags=re.S))
    if found != expected:
        print(f"::error::[{name}] найдено совпадений: {found}, ожидалось: {expected}")
        sys.exit(1)
    src = re.sub(pattern, make, src, flags=re.S)
    print(f"ok: {name}")


BIND_BRANCH = """} else if (position == badgeRow) {
                    int badgeIcon = org.telegram.messenger.BadgeManager.getBadgeIcon(userId);
                    String badgeTitle = org.telegram.messenger.BadgeManager.getTitle(userId);
                    android.text.SpannableStringBuilder badgeText = new android.text.SpannableStringBuilder("  " + (badgeTitle != null ? badgeTitle : ""));
                    if (badgeIcon != 0) {
                        android.graphics.drawable.Drawable badgeDrawable = getContext().getResources().getDrawable(badgeIcon);
                        int badgeSize = AndroidUtilities.dp(26);
                        badgeDrawable.setBounds(0, 0, badgeSize, badgeSize);
                        badgeText.setSpan(new android.text.style.ImageSpan(badgeDrawable, android.text.style.ImageSpan.ALIGN_BOTTOM), 0, 1, android.text.Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
                    }
                    detailCell.setTextAndValue(badgeText, "@ChiperaGram", false);
                """

MENU_METHOD = """    private void showBadgeMenu() {
        if (getParentActivity() == null) {
            return;
        }
        final String downloadLink = "https://t.me/ChiperaGram";
        final String contactLink = "https://t.me/ChiperaGram";
        BottomBuilder builder = new BottomBuilder(getParentActivity());
        builder.addItem("Скачать ChiperaGram", R.drawable.msg_channel, __ -> {
            org.telegram.messenger.browser.Browser.openUrl(getParentActivity(), downloadLink);
            return Unit.INSTANCE;
        });
        builder.addItem("Сотрудничество", R.drawable.msg_discussion, __ -> {
            org.telegram.messenger.browser.Browser.openUrl(getParentActivity(), contactLink);
            return Unit.INSTANCE;
        });
        builder.show();
    }

"""

edit("объявление строки", r"private int idDcRow;",
     lambda m: m.group(0) + "\n    private int badgeRow;")

edit("сброс строки", r"idDcRow = -1;",
     lambda m: m.group(0) + "\n        badgeRow = -1;")

edit("добавление строки в список",
     r"(if \(NaConfig\.INSTANCE\.getIdDcType\(\)\.Int\(\) != 0\) \{\s*idDcRow = rowCount\+\+;\s*\}\s*)(if \(userInfo != null\) \{\s*if \(userInfo\.birthday != null\) \{)",
     lambda m: m.group(1)
     + "if (org.telegram.messenger.BadgeManager.getBadgeIcon(userId) != 0) {\n"
     + "                    badgeRow = rowCount++;\n"
     + "                }\n                "
     + m.group(2))

edit("строка нажимаема", r"return position == notificationRow",
     lambda m: "return position == badgeRow || position == notificationRow")

edit("тип строки", r"position == restrictionReasonRow \|\| position == idDcRow\)",
     lambda m: "position == restrictionReasonRow || position == idDcRow || position == badgeRow)")

edit("позиции для анимации", r"put\(\+\+pointer, idDcRow, sparseIntArray\);",
     lambda m: m.group(0) + "\n        put(++pointer, badgeRow, sparseIntArray);")

edit("нажатие на строку", r"\} else if \(position == idDcRow\) \{(\s*)showIdDcBottomSheet\(\);",
     lambda m: "} else if (position == badgeRow) {\n            showBadgeMenu();\n            return true;\n"
     + "        } else if (position == idDcRow) {" + m.group(1) + "showIdDcBottomSheet();")

edit("отрисовка строки",
     r"\} else if \(position == restrictionReasonRow\) \{(\s*)ArrayList<TLRPC\.RestrictionReason> reasons",
     lambda m: BIND_BRANCH + "} else if (position == restrictionReasonRow) {" + m.group(1)
     + "ArrayList<TLRPC.RestrictionReason> reasons")

edit("меню по нажатию", r"private void showIdDateHint\(View anchor\) \{",
     lambda m: MENU_METHOD + "    private void showIdDateHint(View anchor) {")

PATH.write_text(src, encoding="utf-8")
print("ProfileActivity пропатчен")
