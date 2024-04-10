CREATE TABLE IF NOT EXISTS `user2` (
    `user_id` INT NOT NULL AUTO_INCREMENT,
    `user_type` ENUM(
                        'Administrator',
                        'Health Care Provider',
                        'Intervention Organizer',
                        'Intervention Volunteer',
                        'Policy Maker',
                        'Member'
                ) NOT NULL DEFAULT 'Member',
    `username` TINYTEXT NOT NULL,
    `email` TINYTEXT NOT NULL,
    `password` MEDIUMTEXT NOT NULL,
    `address` LONGTEXT NOT NULL,
    
    PRIMARY KEY (`user_id`),
    UNIQUE (`email`)
);