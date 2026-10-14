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

    private static volatile HashMap<Long, String> badges = new HashMap<>();
    private static volatile boolean cacheLoaded = false;
    private static volatile boolean fetching = false;
    private static volatile long lastFetchTime = 0;

    /** Возвращает значок (эмодзи) для пользователя или null, если значка нет. */
    public static String getBadge(long userId) {
        if (!cacheLoaded) {
            loadCache();
        }
        if (!fetching && System.currentTimeMillis() - lastFetchTime > REFRESH_INTERVAL_MS) {
            refresh();
        }
        return badges.get(userId);
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
                badges = parse(json);
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
                    HashMap<Long, String> parsed = parse(json);
                    badges = parsed;
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

    private static HashMap<Long, String> parse(String json) {
        HashMap<Long, String> result = new HashMap<>();
        try {
            JSONObject root = new JSONObject(json);
            JSONObject types = root.optJSONObject("types");
            JSONObject users = root.optJSONObject("users");
            if (types == null || users == null) {
                return result;
            }
            Iterator<String> keys = users.keys();
            while (keys.hasNext()) {
                String idKey = keys.next();
                String type = users.optString(idKey, "");
                JSONObject typeObject = types.optJSONObject(type);
                if (typeObject == null) {
                    continue;
                }
                String emoji = typeObject.optString("emoji", "");
                if (emoji.isEmpty()) {
                    continue;
                }
                try {
                    result.put(Long.parseLong(idKey.trim()), emoji);
                } catch (NumberFormatException ignore) {
                }
            }
        } catch (Throwable ignore) {
        }
        return result;
    }
                              }
