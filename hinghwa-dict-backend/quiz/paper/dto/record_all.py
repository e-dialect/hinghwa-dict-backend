from ...models import Record


def record_all(record: Record):
    response = {"timestamp": record.timestamp, "correct_answer": record.correct_answer}
    return response
