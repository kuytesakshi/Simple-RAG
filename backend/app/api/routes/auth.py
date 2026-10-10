from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    # TODO: validate user, return JWT
    return {"msg": "login placeholder - implement with DB users table"}

@router.post("/register")
def register():
    # TODO: create user with hashed password
    return {"msg": "register placeholder"}
