from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.authentication.models import User
from app.authentication.schemas import UserCreate
from app.authentication.security import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)


class AuthService:
    
    def create_user(self, user_data: UserCreate, db: Session) -> User:
        try:
            hashed_password = hash_password(user_data.password)
            
            db_user = User(
                username=user_data.username,
                hashed_password=hashed_password,
                role=user_data.role.value
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"Created user: {user_data.username} with role: {user_data.role}")
            return db_user
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating user {user_data.username}: {e}")
            if "username" in str(e.orig).lower():
                raise HTTPException(status_code=400, detail="Username already exists")
            else:
                raise HTTPException(status_code=400, detail="User creation failed")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user {user_data.username}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user")
    
    def authenticate_user(self, username: str, password: str, db: Session) -> User:
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            if not verify_password(password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")
