package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Iterator;

/**
 * Значки для пользователей: список берётся из публичного badges.json на GitHub,
 * кэшируется на телефоне и обновляется не чаще раза в 10 минут.
 */
public class BadgeManager {

    private static final String LIST_URL =
            "https://raw.githubusercontent.com/lastdeqfc-source/chipegram-badges/main/badges.json";
    private static final String PREFS_NAME = "chipegram_badges";
    private static final String PREFS_KEY = "json";
    private static final long REFRESH_INTERVAL_MS = 10 * 60 * 1000L;

    private static class Data {
        final HashMap<Long, String> userTypes = new HashMap<>();
        final HashMap<String, String> titles = new HashMap<>();
        final HashMap<String, String> emojis = new HashMap<>();
    }

    private static volatile Data data = new Data();
    private static volatile boolean cacheLoaded = false;
    private static volatile boolean fetching = false;
    private static volatile long lastFetchTime = 0;

    private static void ensureFresh() {
        if (!cacheLoaded) {
            loadCache();
        }
        if (!fetching && System.currentTimeMillis() - lastFetchTime > REFRESH_INTERVAL_MS) {
            refresh();
        }
    }

    /** Тип значка пользователя: creator, developer, sponsor или null. */
    public static String getType(long userId) {
        ensureFresh();
        return data.userTypes.get(userId);
    }

    /** Название значка («Разработчик») или null, если значка нет. */
    public static String getTitle(long userId) {
        String type = getType(userId);
        if (type == null) {
            return null;
        }
        String title = data.titles.get(type);
        return title != null && !title.isEmpty() ? title : type;
    }

    /** Эмодзи значка (запасной вариант) или null. */
    public static String getBadge(long userId) {
        String type = getType(userId);
        if (type == null) {
            return null;
        }
        return data.emojis.get(type);
    }

    /** Картинка значка (ресурс) или 0, если значка нет. */
    public static int getBadgeIcon(long userId) {
        String type = getType(userId);
        if (type == null) {
            return 0;
        }
        switch (type) {
            case "creator":
                return R.drawable.chipera_badge_creator;
            case "developer":
                return R.drawable.chipera_badge_developer;
            case "sponsor":
                return R.drawable.chipera_badge_sponsor;
            default:
                return 0;
        }
    }

    private static synchronized void loadCache() {
        if (cacheLoaded) {
            return;
        }
        cacheLoaded = true;
        try {
            Context context = ApplicationLoader.applicationContext;
            if (context == null) {
                cacheLoaded = false;
                return;
            }
            SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
            String json = prefs.getString(PREFS_KEY, null);
            if (json != null) {
                data = parse(json);
            }
        } catch (Throwable ignore) {
        }
    }

    private static void refresh() {
        fetching = true;
        lastFetchTime = System.currentTimeMillis();
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(LIST_URL).openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setUseCaches(false);
                if (connection.getResponseCode() == 200) {
                    InputStream in = connection.getInputStream();
                    BufferedReader reader = new BufferedReader(new InputStreamReader(in, "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        sb.append(line).append('\n');
                    }
                    reader.close();
                    String json = sb.toString();
                    data = parse(json);
                    Context context = ApplicationLoader.applicationContext;
                    if (context != null) {
                        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                                .edit().putString(PREFS_KEY, json).apply();
                    }
                }
            } catch (Throwable ignore) {
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
                fetching = false;
            }
        }).start();
    }

    private static Data parse(String json) {
        Data result = new Data();
        try {
            JSONObject root = new JSONObject(json);
            JSONObject types = root.optJSONObject("types");
            JSONObject users = root.optJSONObject("users");
            if (types == null || users == null) {
                return result;
            }
            Iterator<String> typeKeys = types.keys();
            while (typeKeys.hasNext()) {
                String type = typeKeys.next();
                JSONObject typeObject = types.optJSONObject(type);
                if (typeObject == null) {
                    continue;
                }
                result.titles.put(type, typeObject.optString("title", type));
                result.emojis.put(type, typeObject.optString("emoji", ""));
            }
            Iterator<String> keys = users.keys();
            while (keys.hasNext()) {
                String idKey = keys.next();
                String type = users.optString(idKey, "");
                if (!result.titles.containsKey(type)) {
                    continue;
                }
                try {
                    result.userTypes.put(Long.parseLong(idKey.trim()), type);
                } catch (NumberFormatException ignore) {
                }
            }
        } catch (Throwable ignore) {
        }
        return result;
    }
            }
