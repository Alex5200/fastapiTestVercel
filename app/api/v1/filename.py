from datetime import datetime
import uuid


def filenames(file):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"pdf/{timestamp}_{unique_id}_{file.filename}"
