USE marketing_attribution;

CREATE TABLE channels (
    channel_id VARCHAR(20) PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE audiences (
    audience_id VARCHAR(20) PRIMARY KEY,
    audience_name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE campaigns (
    campaign_id VARCHAR(30) PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL,
    objective VARCHAR(100),
    budget DECIMAL(12,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('Planned', 'Active', 'Paused', 'Completed')
        NOT NULL DEFAULT 'Planned',
    CHECK (budget >= 0),
    CHECK (end_date >= start_date)
);

CREATE TABLE campaign_channels (
    campaign_id VARCHAR(30),
    channel_id VARCHAR(20),
    PRIMARY KEY (campaign_id, channel_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

CREATE TABLE creatives (
    creative_id VARCHAR(30) PRIMARY KEY,
    campaign_id VARCHAR(30) NOT NULL,
    creative_name VARCHAR(150) NOT NULL,
    creative_type VARCHAR(50),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE TABLE contacts (
    contact_id VARCHAR(30) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150),
    created_at DATETIME NOT NULL
);