import React, { useCallback, useEffect, useState } from "react";
import { View, Text, FlatList, RefreshControl, StyleSheet } from "react-native";
import { listImages, ImageRecord } from "../api/images";
import StubBadge from "../components/StubBadge";

export default function HistoryScreen() {
  const [items, setItems] = useState<ImageRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await listImages();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    }
  }, []);

  useEffect(() => {
    load().finally(() => setIsLoading(false));
  }, [load]);

  async function onRefresh() {
    setIsRefreshing(true);
    await load();
    setIsRefreshing(false);
  }

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <Text>Loading history…</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.id}
      contentContainerStyle={items.length === 0 ? styles.centered : styles.list}
      refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />}
      ListEmptyComponent={
        <Text style={styles.emptyText}>
          {error ?? "No captures yet — take a photo on the Capture tab."}
        </Text>
      }
      renderItem={({ item }) => (
        <View style={styles.row}>
          <View style={styles.rowText}>
            <Text style={styles.label}>{item.label}</Text>
            <Text style={styles.meta}>
              {new Date(item.createdAt).toLocaleString()} ·{" "}
              {item.confidence !== null
                ? `${(item.confidence * 100).toFixed(1)}%`
                : "confidence n/a"}
            </Text>
          </View>
          <StubBadge stub={item.stub} />
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  centered: { flexGrow: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  list: { padding: 16 },
  emptyText: { color: "#6b7280", textAlign: "center" },
  row: {
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  rowText: { flex: 1, marginRight: 8 },
  label: { fontSize: 16, fontWeight: "600" },
  meta: { fontSize: 12, color: "#6b7280", marginTop: 2 },
});
