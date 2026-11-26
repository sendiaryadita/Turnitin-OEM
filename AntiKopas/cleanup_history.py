"""Wrapper kompatibel: default simulasi, --apply untuk menghapus, --watch berkala.

Aturan penghapusan sama dengan 'python manage.py cleanup_history'.
"""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=float, default=None)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=float, default=None)
    args = parser.parse_args()
    if args.watch and not args.apply:
        parser.error("--watch membutuhkan --apply.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from django.core.management import call_command

    call_command(
        "cleanup_history",
        dry_run=not args.apply,
        hours=args.hours,
        limit=args.limit,
        watch=args.watch,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
