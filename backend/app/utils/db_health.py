"""
Database Health Monitoring Utility
Provides comprehensive health checks and diagnostics for SQLite database
"""
import sqlite3
from datetime import datetime
import os
from typing import Dict, Tuple, Any


def check_database_health(db_path: str = "./gharmitra.db") -> Tuple[bool, Dict[str, Any]]:
    """
    Comprehensive database health check

    Returns:
        (is_healthy: bool, report: dict)

    Example:
        is_healthy, report = check_database_health()
        if not is_healthy:
            print(f"Issues found: {report}")
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "database_path": db_path,
        "checks": {}
    }

    try:
        if not os.path.exists(db_path):
            report["error"] = f"Database file not found: {db_path}"
            report["overall_health"] = "ERROR"
            return False, report

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Integrity check (thorough but slower)
        try:
            cursor.execute("PRAGMA integrity_check")
            integrity_results = cursor.fetchall()
            integrity = integrity_results[0][0] if integrity_results else "unknown"

            report["checks"]["integrity"] = {
                "status": "ok" if integrity == "ok" else "FAILED",
                "result": integrity,
                "details": integrity_results if integrity != "ok" else None
            }
        except Exception as e:
            report["checks"]["integrity"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 2. Quick check (faster version)
        try:
            cursor.execute("PRAGMA quick_check")
            quick = cursor.fetchall()
            report["checks"]["quick_check"] = {
                "status": "ok" if quick[0][0] == "ok" else "FAILED",
                "result": quick[0][0] if quick else "unknown"
            }
        except Exception as e:
            report["checks"]["quick_check"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 3. Check WAL mode
        try:
            cursor.execute("PRAGMA journal_mode")
            journal = cursor.fetchone()[0]
            report["checks"]["journal_mode"] = {
                "status": "ok" if journal == "wal" else "WARNING",
                "value": journal,
                "recommendation": "Enable WAL mode for better crash protection" if journal != "wal" else None
            }
        except Exception as e:
            report["checks"]["journal_mode"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 4. Check synchronous mode
        try:
            cursor.execute("PRAGMA synchronous")
            sync_level = cursor.fetchone()[0]
            sync_names = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
            sync_name = sync_names.get(sync_level, str(sync_level))
            report["checks"]["synchronous"] = {
                "status": "ok" if sync_level in [1, 2] else "WARNING",
                "value": sync_name,
                "recommendation": "NORMAL (1) is recommended with WAL mode" if sync_level != 1 else None
            }
        except Exception as e:
            report["checks"]["synchronous"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 5. Check database size
        try:
            db_size = os.path.getsize(db_path)
            report["checks"]["size"] = {
                "status": "ok",
                "bytes": db_size,
                "mb": round(db_size / (1024*1024), 2),
                "gb": round(db_size / (1024*1024*1024), 4)
            }
        except Exception as e:
            report["checks"]["size"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 6. Check WAL file (if exists)
        try:
            wal_path = db_path + "-wal"
            shm_path = db_path + "-shm"

            wal_exists = os.path.exists(wal_path)
            shm_exists = os.path.exists(shm_path)

            wal_size = os.path.getsize(wal_path) if wal_exists else 0

            report["checks"]["wal_files"] = {
                "status": "ok" if wal_exists and shm_exists else "INFO",
                "wal_exists": wal_exists,
                "shm_exists": shm_exists,
                "wal_size_bytes": wal_size,
                "wal_size_kb": round(wal_size / 1024, 2) if wal_size > 0 else 0,
                "recommendation": "Consider checkpoint if WAL > 10MB" if wal_size > 10*1024*1024 else None
            }
        except Exception as e:
            report["checks"]["wal_files"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 7. Check page count vs freelist (fragmentation)
        try:
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA freelist_count")
            freelist = cursor.fetchone()[0]

            fragmentation = (freelist / page_count * 100) if page_count > 0 else 0

            report["checks"]["fragmentation"] = {
                "status": "ok" if fragmentation < 10 else "WARNING",
                "percent": round(fragmentation, 2),
                "free_pages": freelist,
                "total_pages": page_count,
                "recommendation": "Run VACUUM to reduce fragmentation" if fragmentation > 10 else None
            }
        except Exception as e:
            report["checks"]["fragmentation"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 8. Check cache size
        try:
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]

            # Negative values = KB, positive = pages
            if cache_size < 0:
                cache_mb = abs(cache_size) / 1024
            else:
                # Assume 4KB page size
                cache_mb = (cache_size * 4) / 1024

            report["checks"]["cache_size"] = {
                "status": "ok" if cache_mb >= 2 else "INFO",
                "value": cache_size,
                "mb": round(cache_mb, 2),
                "recommendation": "Increase to -8000 (8MB) for better performance" if cache_mb < 8 else None
            }
        except Exception as e:
            report["checks"]["cache_size"] = {
                "status": "ERROR",
                "error": str(e)
            }

        # 9. Check table count and record counts
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

            table_counts = {}
            total_records = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                    total_records += count
                except:
                    table_counts[table] = "error"

            report["checks"]["tables"] = {
                "status": "ok",
                "table_count": len(tables),
                "total_records": total_records,
                "tables": table_counts
            }
        except Exception as e:
            report["checks"]["tables"] = {
                "status": "ERROR",
                "error": str(e)
            }

        conn.close()

        # Overall health assessment
        critical_checks = ["integrity", "quick_check"]
        has_critical_failure = any(
            report["checks"].get(check, {}).get("status") == "FAILED"
            for check in critical_checks
        )

        has_errors = any(
            check.get("status") == "ERROR"
            for check in report["checks"].values()
        )

        has_warnings = any(
            check.get("status") == "WARNING"
            for check in report["checks"].values()
        )

        if has_critical_failure or has_errors:
            report["overall_health"] = "CRITICAL"
            is_healthy = False
        elif has_warnings:
            report["overall_health"] = "NEEDS_ATTENTION"
            is_healthy = True  # Still healthy but could be optimized
        else:
            report["overall_health"] = "HEALTHY"
            is_healthy = True

        return is_healthy, report

    except Exception as e:
        report["error"] = str(e)
        report["overall_health"] = "ERROR"
        return False, report


def format_health_report(report: Dict[str, Any]) -> str:
    """
    Format health report for human-readable output

    Args:
        report: Report dict from check_database_health()

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"DATABASE HEALTH REPORT - {report.get('timestamp', 'N/A')}")
    lines.append("=" * 70)

    overall = report.get("overall_health", "UNKNOWN")
    emoji = {
        "HEALTHY": "✅",
        "NEEDS_ATTENTION": "⚠️ ",
        "CRITICAL": "❌",
        "ERROR": "💥"
    }.get(overall, "❓")

    lines.append(f"\nOverall Status: {emoji} {overall}")
    lines.append(f"Database: {report.get('database_path', 'N/A')}")

    if "error" in report:
        lines.append(f"\n❌ ERROR: {report['error']}")
        return "\n".join(lines)

    lines.append("\n" + "-" * 70)
    lines.append("CHECK RESULTS:")
    lines.append("-" * 70)

    checks = report.get("checks", {})
    for check_name, check_data in checks.items():
        status = check_data.get("status", "unknown")
        status_emoji = {
            "ok": "✅",
            "WARNING": "⚠️ ",
            "FAILED": "❌",
            "ERROR": "💥",
            "INFO": "ℹ️ "
        }.get(status, "❓")

        lines.append(f"\n{check_name.upper().replace('_', ' ')}:")
        lines.append(f"  Status: {status_emoji} {status}")

        # Show relevant details
        for key, value in check_data.items():
            if key not in ["status", "recommendation", "details", "error"]:
                if isinstance(value, (int, float, str, bool)):
                    lines.append(f"  {key}: {value}")

        # Show recommendation if any
        if "recommendation" in check_data and check_data["recommendation"]:
            lines.append(f"  💡 {check_data['recommendation']}")

        # Show error if any
        if "error" in check_data:
            lines.append(f"  ❌ Error: {check_data['error']}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    # CLI usage
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "./gharmitra.db"

    print(f"Checking database health: {db_path}\n")

    is_healthy, report = check_database_health(db_path)

    print(format_health_report(report))

    # Exit with appropriate code
    if not is_healthy:
        sys.exit(1)
    else:
        sys.exit(0)
