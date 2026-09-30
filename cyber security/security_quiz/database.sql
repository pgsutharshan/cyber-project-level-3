CREATE DATABASE IF NOT EXISTS security_quiz
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE security_quiz;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question TEXT NOT NULL,
  option_a VARCHAR(500) NOT NULL,
  option_b VARCHAR(500) NOT NULL,
  option_c VARCHAR(500) NOT NULL,
  option_d VARCHAR(500) NOT NULL,
  correct_answer CHAR(1) NOT NULL,
  explanation TEXT NOT NULL,
  CONSTRAINT chk_correct_answer CHECK (correct_answer IN ('A', 'B', 'C', 'D'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS quiz_results (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  score INT NOT NULL,
  total_questions INT NOT NULL,
  percentage DECIMAL(5,1) NOT NULL,
  attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_results_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_result_score CHECK (score >= 0 AND score <= total_questions),
  INDEX idx_results_user_date (user_id, attempted_at)
) ENGINE=InnoDB;

-- Sample login: admin@securityquiz.local / Admin@123. Change this password after setup.
INSERT INTO users (name, email, password, role)
VALUES (
  'Security Admin',
  'admin@securityquiz.local',
  'pbkdf2:sha256:600000$security-quiz-admin$d079b8618bdd06426ca436036fa49ba056d175d9be79186300eae2eeb6d021f6',
  'admin'
)
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_answer, explanation) VALUES
('What is the safest response to an unexpected email asking you to verify your account through a link?', 'Click the link if the logo looks familiar', 'Visit the service using a known address and report the email', 'Reply with your account name', 'Forward it to coworkers to ask if it is real', 'B', 'Use a known website address instead of an email link, and report suspicious messages through your organization process.'),
('Which password practice best protects your accounts?', 'Reuse one long password everywhere', 'Use a unique password for every account, stored in a password manager', 'Change one character for each website', 'Share passwords only with teammates', 'B', 'Unique passwords limit the damage when one site is breached. A password manager can create and store them.'),
('What should you do if endpoint protection reports a possible malware infection?', 'Ignore the alert if the computer still works', 'Disconnect from networks if instructed and contact IT/security', 'Download another tool from an unknown site', 'Delete random system files', 'B', 'Follow your organization incident process and avoid actions that could spread the infection or destroy evidence.'),
('A caller claiming to be IT asks for your one-time sign-in code. What should you do?', 'Read the code to them', 'Ask them to confirm your password first', 'Do not share the code; verify the request through an official channel', 'Send a screenshot of the prompt', 'C', 'Legitimate support staff should not need your authentication code. Verify independently using known contact details.'),
('What is a key benefit of multi-factor authentication?', 'It removes the need for software updates', 'It adds another proof of identity beyond a password', 'It encrypts every email automatically', 'It prevents all phishing', 'B', 'MFA adds an additional authentication factor, making a stolen password less sufficient on its own.'),
('When using public Wi-Fi, which action is safest?', 'Disable device updates permanently', 'Use sensitive accounts only over trusted, encrypted connections and avoid unknown prompts', 'Accept every certificate warning', 'Turn off your device firewall', 'B', 'Use HTTPS, a trusted network or approved VPN, and never bypass certificate or security warnings.'),
('What is ransomware designed to do?', 'Improve network speed', 'Encrypt or lock data and demand payment', 'Filter junk email', 'Back up files to a safe location', 'B', 'Ransomware commonly blocks access to data and demands payment. Report suspected incidents immediately.'),
('Before sharing customer information with a new online service, what should you check?', 'Whether it has a modern logo', 'Whether the data is necessary and the service is approved for that information', 'Whether it offers a free trial', 'Whether colleagues use a personal account there', 'B', 'Minimize personal data and use only services approved for the data classification and purpose.'),
('Which practice helps protect a home or office Wi-Fi network?', 'Keep the router default password', 'Use WPA2/WPA3 with a strong unique admin password and updated firmware', 'Broadcast the admin password for convenience', 'Disable encryption for older devices', 'B', 'Strong unique credentials, current firmware, and modern Wi-Fi encryption reduce common network risks.'),
('You receive an attachment you were not expecting from a familiar colleague. What is best?', 'Open it because the sender is known', 'Verify with the colleague using another channel before opening', 'Enable macros if prompted', 'Upload it to a public file-sharing site', 'B', 'A familiar account may be compromised or spoofed. Verify unexpected attachments through a separate trusted channel.'),
('What is the safest way to install a browser extension?', 'Choose one with the most downloads, regardless of permissions', 'Install only from trusted sources and review publisher and requested permissions', 'Use a link from an unsolicited message', 'Grant every permission automatically', 'B', 'Extensions can access browsing data. Review the source, publisher, and permissions before installing.'),
('What should you do with a security update for your operating system?', 'Install it promptly through the official update mechanism', 'Wait until the computer is compromised', 'Download a copy from a pop-up ad', 'Disable update notifications', 'A', 'Timely updates repair known vulnerabilities. Use the operating system or organization-approved update channel.');