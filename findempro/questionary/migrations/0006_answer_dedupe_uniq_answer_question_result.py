from django.db import migrations, models


def dedupe_answers(apps, schema_editor):
    """
    Collapse duplicate answers that share the same (fk_question,
    fk_questionary_result) pair before the unique constraint is applied.

    For each such group we keep a single winner (an active row if any exists,
    otherwise the most recently updated / highest-id row) and hard-delete the
    rest so the constraint can be added cleanly. Idempotent: on a database
    without duplicates it is a no-op.
    """
    Answer = apps.get_model("questionary", "Answer")

    # Find the (question, result) pairs that have more than one answer.
    dup_groups = (
        Answer.objects.values("fk_question_id", "fk_questionary_result_id")
        .annotate(n=models.Count("id"))
        .filter(n__gt=1)
    )

    for group in dup_groups:
        rows = list(
            Answer.objects.filter(
                fk_question_id=group["fk_question_id"],
                fk_questionary_result_id=group["fk_questionary_result_id"],
            )
        )
        if len(rows) < 2:
            continue

        # Prefer an active row; break ties by last_updated then id (most recent).
        def sort_key(a):
            return (
                1 if a.is_active else 0,
                a.last_updated or a.date_created,
                a.id,
            )

        rows.sort(key=sort_key)
        winner = rows[-1]
        losers = [r for r in rows if r.id != winner.id]

        # Keep the winner active if any duplicate was active.
        if not winner.is_active and any(r.is_active for r in rows):
            winner.is_active = True
            winner.save(update_fields=["is_active"])

        Answer.objects.filter(id__in=[r.id for r in losers]).delete()


def noop_reverse(apps, schema_editor):
    """Deduplication cannot be undone; reversing is a no-op."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("questionary", "0005_answer_idx_answer_qresult_active_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe_answers, noop_reverse),
        migrations.AddConstraint(
            model_name="answer",
            constraint=models.UniqueConstraint(
                fields=["fk_question", "fk_questionary_result"],
                name="uniq_answer_question_result",
            ),
        ),
    ]
