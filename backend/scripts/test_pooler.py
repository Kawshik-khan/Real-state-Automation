import psycopg2

regions = [
    "ap-southeast-1", # Singapore
    "ap-south-1",     # Mumbai
    "us-east-1",     # N. Virginia
    "eu-central-1",  # Frankfurt
]

project_ref = "fdjzbtkypedzlkwpzzzt"
user = f"postgres.{project_ref}"

# Test standard candidate passwords
candidate_passwords = [
    "postgres",
    "postgres123",
    "Kawshikkhan25",
    "Kawshik@123",
    "Kawshik123",
    "Abukawshik@gmail.com",
    "Kawshik-khan"
]

print(f"Testing Supabase Pooler for tenant: {user}...")

for region in regions:
    host = f"aws-0-{region}.pooler.supabase.com"
    for pw in candidate_passwords:
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=user,
                password=pw,
                host=host,
                port=6543,
                connect_timeout=3
            )
            print(f"🎉 CONNECTED TO SUPABASE POSTGRESQL!")
            print(f"Region: {region} | Host: {host} | Password match!")
            conn.close()
            exit(0)
        except psycopg2.OperationalError as e:
            err = str(e).strip()
            if "Tenant or user not found" in err:
                print(f"[{region}] Tenant not in this region.")
                break
            elif "password authentication failed" in err:
                # This means the tenant IS in this region!
                print(f"[{region}] Tenant FOUND in this region! (Password was incorrect)")
                break
            else:
                pass
