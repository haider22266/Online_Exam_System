-- Convert application text columns created by SQLAlchemy from VARCHAR to
-- Unicode-capable NVARCHAR. Existing characters already replaced by "?"
-- cannot be recovered and must be regenerated.

ALTER TABLE generated_questions ALTER COLUMN question NVARCHAR(MAX) NOT NULL;
ALTER TABLE generated_questions ALTER COLUMN answer NVARCHAR(MAX) NOT NULL;
ALTER TABLE generated_questions ALTER COLUMN explanation NVARCHAR(MAX) NULL;
ALTER TABLE generated_questions ALTER COLUMN source_document NVARCHAR(255) NULL;
ALTER TABLE generated_questions ALTER COLUMN source_chunk_ids NVARCHAR(MAX) NULL;

ALTER TABLE questions ALTER COLUMN text NVARCHAR(MAX) NOT NULL;
ALTER TABLE questions ALTER COLUMN answer NVARCHAR(MAX) NOT NULL;

ALTER TABLE chunks ALTER COLUMN source_file NVARCHAR(255) NOT NULL;
ALTER TABLE chunks ALTER COLUMN chunk_text NVARCHAR(MAX) NOT NULL;

ALTER TABLE courses ALTER COLUMN title NVARCHAR(200) NOT NULL;
ALTER TABLE courses ALTER COLUMN description NVARCHAR(MAX) NULL;

ALTER TABLE documents ALTER COLUMN original_filename NVARCHAR(255) NOT NULL;
ALTER TABLE documents ALTER COLUMN stored_filename NVARCHAR(255) NOT NULL;
ALTER TABLE documents ALTER COLUMN file_path NVARCHAR(500) NOT NULL;
ALTER TABLE documents ALTER COLUMN error_message NVARCHAR(MAX) NULL;

ALTER TABLE exams ALTER COLUMN title NVARCHAR(200) NOT NULL;
ALTER TABLE student_exam_answers ALTER COLUMN answer_text NVARCHAR(MAX) NULL;
