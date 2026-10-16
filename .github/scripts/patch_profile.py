import re
import sys
from pathlib import Path


def apply(path, marker, edits):
    p = Path(path)
    src = p.read_text(encoding="utf-8")
    if marker in src:
        print(f"{p.name}: уже пропатчен")
        return
    for name, pattern, make in edits:
        found = len(re.findall(pattern, src, flags=re.S))
        if found != 1:
            print(f"::error::[{p.name}: {name}] найдено совпадений: {found}, ожидалось: 1")
            sys.exit(1)
        src = re.sub(pattern, make, src, count=1, flags=re.S)
        print(f"ok: {p.name}: {name}")
    p.write_text(src, encoding="utf-8")


# ---------- профиль: значок перед ником ----------
PROFILE_REPLACEMENT = """android.graphics.drawable.Drawable chipBadgeDrawable = null;
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

apply(
    "TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java",
    "chipBadgeRes",
    [
        ("значок перед ником", r"nameTextView\[a\]\.setLeftDrawable\(leftIcon\);",
         lambda m: PROFILE_REPLACEMENT),
    ],
)

# ---------- кошелёк: локальный баланс ----------
WALLET_HELPERS = '''    private android.content.SharedPreferences chipPrefs() {
        return org.telegram.messenger.ApplicationLoader.applicationContext
                .getSharedPreferences("chipera_wallet", android.content.Context.MODE_PRIVATE);
    }

    private boolean chipLocalEnabled() {
        return chipPrefs().getBoolean("enabled", false)
                && !chipPrefs().getString("gram", "").trim().isEmpty();
    }

    private long chipLocalNanotons(long real) {
        if (!chipLocalEnabled()) {
            return real;
        }
        try {
            String s = chipPrefs().getString("gram", "").trim().replace(',', '.');
            return Math.round(Double.parseDouble(s) * 1000000000d);
        } catch (Throwable t) {
            return real;
        }
    }

    private void chipApplyLocalUsd() {
        if (!chipPrefs().getBoolean("enabled", false)) {
            return;
        }
        String s = chipPrefs().getString("usd", "").trim();
        if (!s.isEmpty() && usdBalanceView != null) {
            usdBalanceView.setText(s);
        }
    }

    private void showLocalBalanceDialog() {
        final android.content.Context ctx = getParentActivity();
        if (ctx == null) {
            return;
        }
        final android.content.SharedPreferences prefs = chipPrefs();
        final android.widget.LinearLayout box = new android.widget.LinearLayout(ctx);
        box.setOrientation(android.widget.LinearLayout.VERTICAL);
        final int pad = org.telegram.messenger.AndroidUtilities.dp(20);
        box.setPadding(pad, pad / 2, pad, 0);

        final android.widget.CheckBox enabled = new android.widget.CheckBox(ctx);
        enabled.setText("Показывать свой баланс (только на этом телефоне)");
        enabled.setChecked(prefs.getBoolean("enabled", false));
        box.addView(enabled);

        final android.widget.EditText gram = new android.widget.EditText(ctx);
        gram.setHint("Сумма GRAM, например 12.5");
        gram.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        gram.setText(prefs.getString("gram", ""));
        box.addView(gram);

        final android.widget.EditText usd = new android.widget.EditText(ctx);
        usd.setHint("В долларах, например $34.20");
        usd.setText(prefs.getString("usd", ""));
        box.addView(usd);

        new android.app.AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                .setTitle("Локальный баланс")
                .setView(box)
                .setPositiveButton("Сохранить", (d, w) -> {
                    prefs.edit()
                            .putBoolean("enabled", enabled.isChecked())
                            .putString("gram", gram.getText().toString())
                            .putString("usd", usd.getText().toString())
                            .apply();
                    update();
                })
                .setNegativeButton("Отмена", null)
                .show();
    }

'''

NOT_READY = """if (!wallet.isReady()) {
            if (chipLocalEnabled()) {
                try {
                    updateBalance(0L);
                    return;
                } catch (Throwable t) {
                    org.telegram.messenger.FileLog.e(t);
                }
            }
            balanceView.setText(loading(0));
            usdBalanceView.setText(loading(1));
            return;
        }"""

apply(
    "TMessagesProj/src/main/java/org/telegram/ui/Wallet/WalletActivity.java",
    "chipLocalNanotons",
    [
        ("сигнатура updateBalance",
         r"private void updateBalance\(long nanotons\) \{",
         lambda m: "private void updateBalance(long realNanotons) {\n        final long nanotons = chipLocalNanotons(realNanotons);"),
        ("сумма в долларах",
         r"(updateBalanceTransitionColors\(balanceTransitionProgress\);)(\s*\}\s*private static class BalanceLabelSpan)",
         lambda m: "chipApplyLocalUsd();\n        " + m.group(1) + m.group(2)),
        ("кошелёк не готов",
         r"if \(!wallet\.isReady\(\)\) \{\s*balanceView\.setText\(loading\(0\)\);\s*usdBalanceView\.setText\(loading\(1\)\);\s*return;\s*\}",
         lambda m: NOT_READY),
        ("пункт меню",
         r"(final ItemOptions o = ItemOptions\.makeOptions\(WalletActivity\.this, v, true\);\s*o\.translate\(0, -dp\(48\)\);\s*o\.setDimAlpha\(0\);\s*o\.setGravity\(Gravity\.RIGHT\);)",
         lambda m: m.group(1) + '\n                o.add(R.drawable.msg_edit, "Локальный баланс", () -> showLocalBalanceDialog());'),
        ("вспомогательные методы",
         r"private void setUse2DCard\(boolean use2D\) \{",
         lambda m: WALLET_HELPERS + "    private void setUse2DCard(boolean use2D) {"),
    ],
)

print("готово")
