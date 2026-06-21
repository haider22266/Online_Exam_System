CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(120) NOT NULL,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(20) NOT NULL DEFAULT 'teacher',
    is_active_flag BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE courses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    code NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(MAX),
    teacher_id INT NULL REFERENCES users(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(id),
    original_filename NVARCHAR(255) NOT NULL,
    stored_filename NVARCHAR(255) NOT NULL,
    file_path NVARCHAR(500) NOT NULL,
    file_type NVARCHAR(20) NOT NULL,
    page_count INT NOT NULL DEFAULT 0,
    status NVARCHAR(30) NOT NULL DEFAULT 'uploaded',
    error_message NVARCHAR(MAX),
    uploaded_by_id INT NOT NULL REFERENCES users(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE chunks (
    id INT IDENTITY(1,1) PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(id),
    document_id INT NOT NULL REFERENCES documents(id),
    chunk_index INT NOT NULL,
    source_file NVARCHAR(255) NOT NULL,
    page_number INT NULL,
    chunk_text NVARCHAR(MAX) NOT NULL,
    chroma_id NVARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE questions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    text NVARCHAR(MAX) NOT NULL,
    answer NVARCHAR(MAX) NOT NULL,
    difficulty NVARCHAR(20) NOT NULL,
    question_type NVARCHAR(40) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE generated_questions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(id),
    question NVARCHAR(MAX) NOT NULL,
    answer NVARCHAR(MAX) NOT NULL,
    explanation NVARCHAR(MAX),
    difficulty NVARCHAR(20) NOT NULL,
    predicted_difficulty NVARCHAR(20),
    question_type NVARCHAR(40) NOT NULL,
    source_document NVARCHAR(255),
    source_chunk_ids NVARCHAR(MAX),
    created_by_id INT NOT NULL REFERENCES users(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE exams (
    id INT IDENTITY(1,1) PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(id),
    title NVARCHAR(200) NOT NULL,
    total_marks INT NOT NULL DEFAULT 0,
    created_by_id INT NOT NULL REFERENCES users(id),
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE exam_questions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    exam_id INT NOT NULL REFERENCES exams(id),
    generated_question_id INT NOT NULL REFERENCES generated_questions(id),
    marks INT NOT NULL DEFAULT 1,
    sort_order INT NOT NULL DEFAULT 0
);
