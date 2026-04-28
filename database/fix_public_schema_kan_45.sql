ALTER TABLE documents
DROP COLUMN canvas_file_id;

ALTER TABLE users
    DROP COLUMN canvas_user_id;

ALTER TABLE courses
    DROP COLUMN canvas_id;

<<<<<<< Updated upstream
ALTER TABLE users
    ADD COLUMN password VARCHAR(64) NOT NULL;


=======


ALTER TABLE users
    ADD COLUMN password VARCHAR(64) NOT NULL DEFAULT '';


DELETE * FROM users
>>>>>>> Stashed changes

