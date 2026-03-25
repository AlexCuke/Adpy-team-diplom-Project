from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, BigInteger, String, DateTime,
    Date, Text, Boolean, ForeignKey, UniqueConstraint,
    CheckConstraint, select
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session, joinedload
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    likes_given = relationship("Like", foreign_keys="Like.liker_id", back_populates="liker",
                               cascade="all, delete-orphan")
    likes_received = relationship("Like", foreign_keys="Like.liked_id", back_populates="liked")
    matches_as_user1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1",
                                    cascade="all, delete-orphan")
    matches_as_user2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")


class Profile(Base):
    __tablename__ = 'profiles'

    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)

    # Relationship
    user = relationship("User", back_populates="profile")


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    url = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="photos")


class Like(Base):
    __tablename__ = 'likes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    liker_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    liked_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    liker = relationship("User", foreign_keys=[liker_id], back_populates="likes_given")
    liked = relationship("User", foreign_keys=[liked_id], back_populates="likes_received")

    # Constraints
    __table_args__ = (
        UniqueConstraint('liker_id', 'liked_id', name='uq_likes'),
        CheckConstraint('liker_id <> liked_id', name='chk_no_self_like'),
    )


class Match(Base):
    __tablename__ = 'matches'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user2_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    messages = relationship("Message", back_populates="match", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='uq_matches'),
        CheckConstraint('user1_id <> user2_id', name='chk_no_self_match'),
        CheckConstraint('user1_id < user2_id', name='chk_user_order'),
    )


class Message(Base):
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    match_id = Column(BigInteger, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    match = relationship("Match", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")


class DatabaseORM:
    """ORM класс для работы с базой данных"""

    def __init__(self, database_url: str, echo: bool = False):
        """
        Инициализация подключения к базе данных

        Args:
            database_url: URL для подключения к БД (например, 'postgresql://user:pass@localhost/dbname')
            echo: Включать ли логирование SQL запросов
        """
        self.engine = create_engine(database_url, echo=echo)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Создание всех таблиц в базе данных"""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Удаление всех таблиц из базы данных (осторожно!)"""
        Base.metadata.drop_all(self.engine)

    def get_session(self) -> Session:
        """Получение новой сессии для работы с БД"""
        return self.SessionLocal()

    # ============= User operations =============

    def create_user(self, email: str, password_hash: str) -> Optional[User]:
        """Создание нового пользователя"""
        session = self.get_session()
        try:
            user = User(email=email, password_hash=password_hash)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def update_last_login(self, user_id: int) -> bool:
        """Обновление времени последнего входа"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.now(timezone.utc)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # ============= Profile operations =============

    def create_or_update_profile(self, user_id: int, **kwargs) -> Optional[Profile]:
        """Создание или обновление профиля пользователя"""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile:
                profile = Profile(user_id=user_id, **kwargs)
                session.add(profile)
            else:
                for key, value in kwargs.items():
                    if hasattr(profile, key) and value is not None:
                        setattr(profile, key, value)
            session.commit()
            session.refresh(profile)
            return profile
        finally:
            session.close()

    def get_profile(self, user_id: int) -> Optional[Profile]:
        """Получение профиля пользователя"""
        session = self.get_session()
        try:
            return session.query(Profile).filter(Profile.user_id == user_id).first()
        finally:
            session.close()

    # ============= Photo operations =============

    def add_photo(self, user_id: int, url: str, is_primary: bool = False) -> Optional[Photo]:
        """Добавление фотографии пользователя"""
        session = self.get_session()
        try:
            # Если это основное фото, снимаем флаг с других фото
            if is_primary:
                session.query(Photo).filter(Photo.user_id == user_id).update({'is_primary': False})

            photo = Photo(user_id=user_id, url=url, is_primary=is_primary)
            session.add(photo)
            session.commit()
            session.refresh(photo)
            return photo
        finally:
            session.close()

    def get_user_photos(self, user_id: int) -> List[Photo]:
        """Получение всех фото пользователя"""
        session = self.get_session()
        try:
            return session.query(Photo).filter(Photo.user_id == user_id).order_by(Photo.created_at).all()
        finally:
            session.close()

    def set_primary_photo(self, photo_id: int, user_id: int) -> bool:
        """Установка основного фото"""
        session = self.get_session()
        try:
            # Снимаем флаг со всех фото пользователя
            session.query(Photo).filter(Photo.user_id == user_id).update({'is_primary': False})
            # Устанавливаем новое основное фото
            session.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).update({'is_primary': True})
            session.commit()
            return True
        finally:
            session.close()

    # ============= Like operations =============

    def add_like(self, liker_id: int, liked_id: int) -> Optional[Dict[str, Any]]:
        """
        Добавление лайка. Возвращает словарь с информацией о матче, если он произошел
        """
        if liker_id == liked_id:
            return None

        session = self.get_session()
        try:
            # Проверяем, существует ли уже лайк
            existing_like = session.query(Like).filter(
                Like.liker_id == liker_id, Like.liked_id == liked_id
            ).first()

            if existing_like:
                return None

            # Добавляем лайк
            like = Like(liker_id=liker_id, liked_id=liked_id)
            session.add(like)

            # Проверяем, есть ли взаимный лайк
            mutual_like = session.query(Like).filter(
                Like.liker_id == liked_id, Like.liked_id == liker_id
            ).first()

            match_created = False
            if mutual_like:
                # Создаем матч
                user1_id, user2_id = sorted([liker_id, liked_id])
                match = Match(user1_id=user1_id, user2_id=user2_id)
                session.add(match)
                session.flush()
                match_created = True

            session.commit()

            result = {'like_created': True}
            if match_created:
                result['match_created'] = True
                result['match'] = self.get_match_between_users(liker_id, liked_id, session)

            return result

        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()

    def remove_like(self, liker_id: int, liked_id: int) -> bool:
        """Удаление лайка"""
        session = self.get_session()
        try:
            result = session.query(Like).filter(
                Like.liker_id == liker_id, Like.liked_id == liked_id
            ).delete()
            session.commit()
            return result > 0
        finally:
            session.close()

    def get_user_likes_given(self, user_id: int) -> List[Like]:
        """Получение всех лайков, поставленных пользователем"""
        session = self.get_session()
        try:
            return session.query(Like).filter(Like.liker_id == user_id).all()
        finally:
            session.close()

    # ============= Match operations =============

    def get_match_between_users(self, user1_id: int, user2_id: int, session: Optional[Session] = None) -> Optional[
        Match]:
        """Получение матча между двумя пользователями"""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            user1_id, user2_id = sorted([user1_id, user2_id])
            return session.query(Match).filter(
                Match.user1_id == user1_id,
                Match.user2_id == user2_id
            ).first()
        finally:
            if close_session:
                session.close()

    def get_user_matches(self, user_id: int) -> List[Match]:
        """Получение всех матчей пользователя"""
        session = self.get_session()
        try:
            matches = session.query(Match).filter(
                (Match.user1_id == user_id) | (Match.user2_id == user_id)
            ).all()
            return matches
        finally:
            session.close()

    def get_match_with_details(self, match_id: int) -> Optional[Match]:
        """Получение матча с полной информацией о пользователях и сообщениях"""
        session = self.get_session()
        try:
            return session.query(Match).options(
                joinedload(Match.user1),
                joinedload(Match.user2),
                joinedload(Match.messages)
            ).filter(Match.id == match_id).first()
        finally:
            session.close()

    # ============= Message operations =============

    def send_message(self, match_id: int, sender_id: int, content: str) -> Optional[Message]:
        """Отправка сообщения"""
        session = self.get_session()
        try:
            # Проверяем, что пользователь является участником матча
            match = session.query(Match).filter(Match.id == match_id).first()
            if not match or (match.user1_id != sender_id and match.user2_id != sender_id):
                return None

            message = Message(match_id=match_id, sender_id=sender_id, content=content)
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()

    def get_match_messages(self, match_id: int, limit: int = 50, offset: int = 0) -> List[Message]:
        """Получение сообщений матча с пагинацией"""
        session = self.get_session()
        try:
            return session.query(Message).filter(Message.match_id == match_id) \
                .order_by(Message.sent_at.desc()) \
                .offset(offset).limit(limit).all()
        finally:
            session.close()

    # ============= Search and filters =============

    def search_users(self,
                     age_min: Optional[int] = None,
                     age_max: Optional[int] = None,
                     gender: Optional[str] = None,
                     city: Optional[str] = None,
                     limit: int = 20) -> List[User]:
        """Поиск пользователей с фильтрацией"""
        session = self.get_session()
        try:
            query = session.query(User).join(Profile, isouter=True)

            if gender:
                query = query.filter(Profile.gender == gender)

            if city:
                query = query.filter(Profile.city.ilike(f"%{city}%"))

            if age_min or age_max:
                # Фильтрация по возрасту через дату рождения
                today = date.today()
                if age_min:
                    max_birth_date = date(today.year - age_min, today.month, today.day)
                    query = query.filter(Profile.birth_date <= max_birth_date)
                if age_max:
                    min_birth_date = date(today.year - age_max - 1, today.month, today.day)
                    query = query.filter(Profile.birth_date >= min_birth_date)

            return query.limit(limit).all()
        finally:
            session.close()

    def get_potential_matches(self, user_id: int, limit: int = 20) -> List[User]:
        """Получение потенциальных матчей (пользователи, которых пользователь еще не лайкнул)"""
        session = self.get_session()
        try:
            # Получаем пользователей, которых еще не лайкнули
            query = session.query(User).join(Profile, isouter=True).filter(
                User.id != user_id,
                User.id.notin_(
                    select(Like.liked_id).filter(Like.liker_id == user_id)
                )
            )
            return query.limit(limit).all()
        finally:
            session.close()
