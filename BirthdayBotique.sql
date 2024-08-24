-- Table to store user information
CREATE TABLE Users (
    ChatID BIGINT PRIMARY KEY,                         -- Unique identifier for each user
    DOB DATE NOT NULL,                                 -- Date of Birth (Required)
    CustomMessage NVARCHAR(MAX) NULL,                  -- Optional custom birthday message
    CreatedAt DATETIME DEFAULT GETDATE() NOT NULL,     -- Timestamp of record creation
    UpdatedAt DATETIME DEFAULT GETDATE() NOT NULL      -- Timestamp of last update
);

-- Table to store logs of user actions
CREATE TABLE Logs (
    LogID INT PRIMARY KEY IDENTITY(1,1),               -- Auto-incremented unique identifier for each log entry
    ChatID BIGINT NOT NULL,                            -- Identifier linking to the Users table
    Action NVARCHAR(500) NOT NULL,                     -- Description of the action performed
    Timestamp DATETIME DEFAULT GETDATE() NOT NULL,     -- Timestamp of when the action occurred
    CONSTRAINT FK_Logs_Users FOREIGN KEY (ChatID) REFERENCES Users(ChatID) ON DELETE CASCADE
);

-- Indexes for optimized performance on frequently queried columns
CREATE INDEX IDX_Logs_ChatID ON Logs(ChatID);          -- Index on ChatID in Logs table
CREATE INDEX IDX_Users_DOB ON Users(DOB);              -- Index on DOB in Users table
CREATE INDEX IDX_Logs_Timestamp ON Logs(Timestamp);    -- Index on Timestamp in Logs table

-- Trigger to automatically update the UpdatedAt field in Users table when a record is modified
CREATE TRIGGER trg_UpdateTimestamp
ON Users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Update the UpdatedAt column to the current date/time
    UPDATE Users
    SET UpdatedAt = GETDATE()
    WHERE ChatID IN (SELECT DISTINCT ChatID FROM Inserted);
END;
