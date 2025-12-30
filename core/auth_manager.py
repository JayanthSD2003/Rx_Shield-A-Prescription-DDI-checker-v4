import bcrypt
from core.database import add_user, get_user, init_db, log_login, update_user_password

# Initialize DB on module load (or call explicitly in main)
init_db()

def register(username, password, role='User'):
    if not username or not password:
        return False, "Username and password are required."
    
    if get_user(username):
        return False, "Username already exists."

    # Hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Auto-approve 'User' role if not specified otherwise, but requirement says "new user, doc registration approvals"
    # So 'User' and 'Doctor' need approval. 'Admin' likely needs approval too if registered via UI.
    # RootAdmin is pre-seeded.
    # Let's set is_approved=0 for everyone except maybe RootAdmin (handled in seed).
    is_approved = 0
    
    if add_user(username, hashed.decode('utf-8'), role, is_approved):
        return True, "Registration successful. Please wait for admin approval."
    else:
        return False, "Registration failed."

def login(username, password):
    user = get_user(username)
    if user:
        if not user['is_approved']:
            log_login(username, "Failed - Not Approved")
            return False, "Account not approved yet.", None
            
        stored_hash = user['password_hash'].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            log_login(username, "Success")
            return True, "Login successful.", user['role']
        else:
            log_login(username, "Failed - Invalid Credentials")
            return False, "Invalid username or password.", None
    
    log_login(username, "Failed - User Not Found")
    return False, "Invalid username or password.", None
    if not user:
         log_login(username, "Failed - User Not Found")

    return False, "Invalid username or password.", None

def change_password(username, new_password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
    update_user_password(username, hashed.decode('utf-8'))
    return True, "Password updated successfully."

def admin_create_user(creator_role, username, password, role):
    if not username or not password:
        return False, "Username and password required."
    
    # 1. Check Admin Limit if creating an Admin
    if role == 'Admin':
        if creator_role != 'RootAdmin':
            return False, "Only RootAdmin can create Admins."
        
        from core.database import get_admin_count
        count = get_admin_count()
        if count >= 3:
            return False, "Admin limit reached (Max 3)."

    # 2. Check Permissions for other roles
    if role in ['User', 'Doctor'] and creator_role not in ['Admin', 'RootAdmin']:
        return False, "Unauthorized action."

    # 3. Create User (Auto-Approved)
    if get_user(username):
        return False, "Username already exists."

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Direct creation by admin implies approval
    if add_user(username, hashed.decode('utf-8'), role, is_approved=1):
        return True, f"{role} created successfully."
    else:
        return False, "Creation failed."
