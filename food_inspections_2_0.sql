#DROP DATABASE food_inspections;

CREATE DATABASE IF NOT EXISTS food_inspections;

USE food_inspections;

-- the parent of all, so it does not need a foreign key
CREATE TABLE census_tract (
	tract_id CHAR(11) PRIMARY KEY,
    census_year YEAR
);

CREATE TABLE census_block_group (
	block_group_id CHAR(12) PRIMARY KEY,
    census_year YEAR,
    tract_id CHAR(11),
    CONSTRAINT joins_tract
		FOREIGN KEY (tract_id)
        REFERENCES census_tract(tract_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE census_block (
	block_id CHAR(15) PRIMARY KEY,
    block_group_id CHAR(12),
	census_year YEAR, -- remains expandable to view changes across different census years.
    CONSTRAINT joins_block_group
		FOREIGN KEY (block_group_id)
        REFERENCES census_block_group(block_group_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE land_parcel (
	land_parcel_id CHAR(10) PRIMARY KEY,
    gis_id CHAR(10) UNIQUE, -- ALTERNATE KEY    
    block_id CHAR(15),
    CONSTRAINT joins_block
		FOREIGN KEY (block_id)
        REFERENCES census_block(block_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- 1: between address and land_parcel 
	-- combine into one relation?
    -- 
CREATE TABLE restaurant (
	-- restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
    license_num INT PRIMARY KEY,
    -- property_id INT, -- one restaurant can have many property_id's!
    issue_date DATETIME,
    expiration_date DATETIME,
    license_status ENUM('active', 'inactive'),
    license_type ENUM('FS', 'FT', 'MFW'),
	business_name VARCHAR(512) UNIQUE,
    legal_owner VARCHAR(256),
    contact_first VARCHAR(256),
    contact_last VARCHAR(256),
    price_level VARCHAR(16)
    -- restaurant_type VARCHAR(256) -- cuisine
);

CREATE TABLE address (
	property_id INT PRIMARY KEY,  -- is in dataset
    license_num INT,
    land_parcel_id CHAR(10),    
	street_num VARCHAR(128),
    city VARCHAR(128),
    state VARCHAR(2),
    zip CHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    CONSTRAINT join_land_parcel
		FOREIGN KEY (land_parcel_id)
        REFERENCES land_parcel(land_parcel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
	CONSTRAINT address_join_restaurant
		FOREIGN KEY (license_num)
        REFERENCES restaurant(license_num)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE inspection (
	inspection_id INT AUTO_INCREMENT PRIMARY KEY,
    license_num INT,
	result VARCHAR(32),
    result_datetime DATETIME,
	UNIQUE ( license_num, result_datetime),
    CONSTRAINT join_restaurant
		FOREIGN KEY (license_num)
        REFERENCES restaurant(license_num)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE violation (
	type_code VARCHAR(32) PRIMARY KEY,
    inspection_id INT,
	violation_status ENUM('pass', 'fail'), -- can be null if passed
    status_date DATE,
	violation_comment TEXT,   
    type_description VARCHAR(256) UNIQUE,
    violation_level ENUM('1', '2', '3'), -- can be null (some legit '-' for code L1)
    CONSTRAINT join_inspection
		FOREIGN KEY (inspection_id)
        REFERENCES inspection(inspection_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

/*CREATE TABLE license (
	license_num INT PRIMARY KEY,
    issue_date DATE,
    expiration_date DATE,
    license_status ENUM('active', 'inactive'),
    license_type ENUM('FS', 'FT', 'MFW')
);*/

CREATE TABLE app_user (
	username VARCHAR(32) PRIMARY KEY,
    user_password VARCHAR(32),
    home_city VARCHAR(32),
    home_state CHAR(2)
);

/*
CONSTRAINT joins_pupil_fk
		FOREIGN KEY (pupil_id)
        REFERENCES pupil(pupil_id)
        ON UPDATE CASCADE ON DELETE NO ACTION,
*/

-- a many to many relationship (*:*)
CREATE TABLE review (
	license_num INT,
    username VARCHAR(32),
    PRIMARY KEY(license_num, username),
    review_comment TEXT,
    rating ENUM('0', '1', '2', '3', '4', '5'),
    review_date DATE,
    CONSTRAINT joins_restaurant_fk
		FOREIGN KEY (license_num)
        REFERENCES restaurant(license_num)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
	CONSTRAINT joins_app_user_fk
		FOREIGN KEY (username)
        REFERENCES app_user(username)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);


-- FUNCTIONS

DELIMITER //

DROP FUNCTION IF EXISTS row_counter//
CREATE FUNCTION row_counter
(
	count_table VARCHAR(50)
)
RETURNS int
DETERMINISTIC READS SQL DATA
BEGIN
	DECLARE rows_count_var INT;
    SELECT COUNT(*)
    INTO rows_count_var
    FROM count_table;
    
    RETURN(rows_count_var);
    
END//


