-- Хранит данные для авторизации.
CREATE TABLE Users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Информация, которую видят другие пользователи.
-- Аватар вынесен в таблицу Photos
CREATE TABLE Profiles (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(20),
    bio TEXT,
    city VARCHAR(100),

    CONSTRAINT fk_profiles_user
        FOREIGN KEY (user_id)
        REFERENCES Users(id)
        ON DELETE CASCADE
);

-- Фиксирует, кто кого лайкнул.
CREATE TABLE Likes (
    id BIGSERIAL PRIMARY KEY,
    liker_id BIGINT NOT NULL,
    liked_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_likes UNIQUE (liker_id, liked_id),

    CONSTRAINT fk_likes_liker
        FOREIGN KEY (liker_id)
        REFERENCES Users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_likes_liked
        FOREIGN KEY (liked_id)
        REFERENCES Users(id)
        ON DELETE CASCADE,
        
    -- Нельзя лайкать себя
    CONSTRAINT chk_no_self_like CHECK (liker_id <> liked_id)
);

-- Фиксируем факт мэтча (чтобы не считать каждый раз).
CREATE TABLE Matches (
    id BIGSERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_matches UNIQUE (user1_id, user2_id),

    CONSTRAINT fk_matches_user1
        FOREIGN KEY (user1_id)
        REFERENCES Users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_matches_user2
        FOREIGN KEY (user2_id)
        REFERENCES Users(id)
        ON DELETE CASCADE,
    
    -- Проверка на мэтч на самого себя
    CONSTRAINT chk_no_self_match CHECK (user1_id <> user2_id),
    
    -- Фиксируем порядок, чтобы избежать дублей (A-B и B-A)
    CONSTRAINT chk_user_order CHECK (user1_id < user2_id)
);

-- Сообщения пользователей
-- сообщения привязаны к мэтчу
-- нельзя писать без взаимного лайка
CREATE TABLE Messages (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,
    sender_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_messages_match
        FOREIGN KEY (match_id)
        REFERENCES Matches(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_messages_sender
        FOREIGN KEY (sender_id)
        REFERENCES Users(id)
        ON DELETE CASCADE
);

-- Фотографии пользователей
CREATE TABLE Photos (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    url TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE, -- TRUE если фото - аватар
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_photos_user
        FOREIGN KEY (user_id)
        REFERENCES Users(id)
        ON DELETE CASCADE
);