import re
import sys
from pathlib import Path

PATH = Path("TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java")
src = PATH.read_text(encoding="utf-8")

if "chipBadgeRes" in src:
    print("ProfileActivity уже пропатчен")
    sys.exit(0)

PATTERN = r"nameTextView\[a\]\.setLeftDrawable\(leftIcon\);"
found = len(re.findall(PATTERN, src))
if found != 1:
    print(f"::error::[значок перед ником] найдено совпадений: {found}, ожидалось: 1")
    sys.exit(1)

REPLACEMENT = """android.graphics.drawable.Drawable chipBadgeDrawable = null;
                if (leftIcon == null) {
                    final int chipBadgeRes = org.telegram.messenger.BadgeManager.getBadgeIcon(user.id);
                    if (chipBadgeRes != 0) {
                        final int chipBadgeSize = AndroidUtilities.dp(22);
                        android.graphics.drawable.BitmapDrawable chipBitmapDrawable = new android.graphics.drawable.BitmapDrawable(getContext().getResources(), android.graphics.BitmapFactory.decodeResource(getContext().getResources(), chipBadgeRes)) {
                            @Override
                            public int getIntrinsicWidth() {
                                return chipBadgeSize;
                            }

                            @Override
                            public int getIntrinsicHeight() {
                                return chipBadgeSize;
                            }
                        };
                        chipBitmapDrawable.setFilterBitmap(true);
                        chipBadgeDrawable = chipBitmapDrawable;
                    }
                }
                nameTextView[a].setLeftDrawable(leftIcon != null ? leftIcon : chipBadgeDrawable);"""

src = re.sub(PATTERN, lambda m: REPLACEMENT, src)
PATH.write_text(src, encoding="utf-8")
print("ok: значок перед ником добавлен")
