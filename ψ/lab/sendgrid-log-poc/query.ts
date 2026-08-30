import { join } from "path";
import { Database } from "bun:sqlite";

const db = new Database(join(import.meta.dir, "events.db"));

const summary = db
  .query("SELECT event, COUNT(*) as n FROM events GROUP BY event ORDER BY n DESC")
  .all();
console.table(summary);

const oldest = db.query("SELECT MIN(ts) as first_seen FROM events").get() as { first_seen: number | null };
if (oldest.first_seen) {
  console.log("เก็บข้อมูลมาแล้วตั้งแต่:", new Date(oldest.first_seen * 1000).toISOString());
} else {
  console.log("ยังไม่มี event ในฐานข้อมูล");
}
