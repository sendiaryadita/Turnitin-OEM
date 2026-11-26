from django.contrib.staticfiles.management.commands.runserver import Command as StaticRunserver

from detector.services.history_cleanup import start_cleanup_worker


class Command(StaticRunserver):
    """Worker hanya dimulai pada proses server, bukan proses induk autoreloader."""

    def inner_run(self, *args, **options):
        stop, worker = start_cleanup_worker()
        self.stdout.write("Cleanup riwayat otomatis aktif.")
        try:
            return super().inner_run(*args, **options)
        finally:
            stop.set()
            worker.join(timeout=5)
