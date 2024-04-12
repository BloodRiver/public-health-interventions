CREATE TABLE IF NOT EXISTS `user` (
    `user_id` INT NOT NULL AUTO_INCREMENT , 
    `username` TINYTEXT NOT NULL , 
    `email` TINYTEXT NOT NULL , 
    `phone_number` TINYTEXT NOT NULL , 
    `password` LONGTEXT NOT NULL , 
    `address` LONGTEXT NOT NULL , 
    `user_type` CHAR(4) NOT NULL , 
    PRIMARY KEY (`user_id`)
);

CREATE TABLE IF NOT EXISTS intervention (
    intervention_id INT NOT NULL AUTO_INCREMENT,
    organizer_id INT NOT NULL,
    start_date DATE,
    end_date DATE,
    event_name TEXT NOT NULL,
    event_venue TEXT NOT NULL,
    event_details LONGTEXT NOT NULL,
    event_status ENUM ('Upcoming', 'Ongoing', 'Cancelled', 'Postpones', 'Completed'),
    PRIMARY KEY (intervention_id),
    FOREIGN KEY (organizer_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS article (
    article_id INT NOT NULL AUTO_INCREMENT,
    author_id INT NOT NULL,
    title TINYTEXT NOT NULL,
    date_published DATE NOT NULL,
    content LONGTEXT NOT NULL,
    article_type CHAR(2) NOT NULL,
    PRIMARY KEY (article_id),
    FOREIGN KEY (author_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS intervention_participation (
    volunteer_id INT NOT NULL,
    intervention_id INT NOT NULL,
    volunteer_present BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (volunteer_id) REFERENCES user(user_id),
    FOREIGN KEY (intervention_id) REFERENCES intervention(intervention_id)
);

CREATE TABLE IF NOT EXISTS intervention_result (
    result_id INT NOT NULL AUTO_INCREMENT,
    author_id INT NOT NULL,
    intervention_id INT NOT NULL,
    before_intervention_description LONGTEXT NOT NULL,
    after_intervention_description LONGTEXT NOT NULL,
    PRIMARY KEY (result_id),
    FOREIGN KEY (author_id) REFERENCES user(user_id),
    FOREIGN KEY (intervention_id) REFERENCES intervention(intervention_id)
);

CREATE TABLE IF NOT EXISTS chart (
    chart_id INT NOT NULL AUTO_INCREMENT,
    author_id INT NOT NULL,
    result_id INT NOT NULL,
    chart_type CHAR(3) NOT NULL DEFAULT "BV",
    `data` LONGTEXT NOT NULL,
    chart_placement CHAR(2) NOT NULL DEFAULT 'B',
    PRIMARY KEY (chart_id),
    FOREIGN KEY (author_id) REFERENCES user(user_id),
    FOREIGN KEY (result_id) REFERENCES intervention_result(result_id)
);

CREATE TABLE IF NOT EXISTS intervention_report (
    report_id INT NOT NULL AUTO_INCREMENT,
    author_id INT NOT NULL,
    intervention_id INT NOT NULL,
    date_reported DATE NOT NULL DEFAULT CURRENT_DATE,
    report_title TINYTEXT NOT NULL,
    report_content LONGTEXT NOT NULL,
    PRIMARY KEY (report_id),
    FOREIGN KEY (author_id) REFERENCES user(user_id),
    FOREIGN KEY (intervention_id) REFERENCES intervention(intervention_id)
);
