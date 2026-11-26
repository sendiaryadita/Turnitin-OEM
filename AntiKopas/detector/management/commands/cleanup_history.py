import math
from threading import Event

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from detector.services.history_cleanup import cleanup_expired_analyses, run_cleanup_loop


class Command(BaseCommand):
    help = "Hapus analisis kedaluwarsa dan file terkait; --watch untuk worker berkala."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Simulasi tanpa menghapus data.")
        parser.add_argument("--hours", type=float, default=None, help="Override retensi hasil (jam).")
        parser.add_argument("--limit", type=int, default=1000, help="Batas job per putaran sekali jalan.")
        parser.add_argument("--watch", action="store_true", help="Bersihkan terus sampai Ctrl+C.")
        parser.add_argument("--interval", type=float, default=None, help="Interval worker dalam detik.")

    def handle(self, *args, **options):
        hours = options["hours"] if options["hours"] is not None else settings.ANALYSIS_RETENTION_HOURS
        interval = options["interval"] if options["interval"] is not None else settings.HISTORY_CLEANUP_INTERVAL_SECONDS
        if not all(math.isfinite(value) and value > 0 for value in (hours, interval)):
            raise CommandError("--hours dan --interval harus berupa angka positif.")
        if options["limit"] <= 0:
            raise CommandError("--limit harus lebih dari 0.")
        if options["watch"] and (options["dry_run"] or options["limit"] != 1000):
            raise CommandError("--watch tidak digabung dengan --dry-run atau --limit.")

        with override_settings(ANALYSIS_RETENTION_HOURS=hours):
            if options["watch"]:
                self.stdout.write(f"Worker cleanup aktif, interval {interval:g} detik. Ctrl+C untuk berhenti.")
                try:
                    run_cleanup_loop(Event(), interval)
                except KeyboardInterrupt:
                    self.stdout.write("Worker cleanup dihentikan.")
                return
            result = cleanup_expired_analyses(
                dry_run=options["dry_run"], limit=options["limit"]
            )
        mode = "DRY RUN" if options["dry_run"] else "DELETE"
        self.stdout.write(
            f"{mode} | kandidat={result['candidates']} | "
            f"dihapus={result['deleted']} | gagal={result['errors']}"
        )
        if result["errors"]:
            raise CommandError("Sebagian file gagal dihapus; data disisakan untuk dicoba ulang.")
