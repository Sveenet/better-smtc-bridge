"""Install into the active isolated environment; IPv4 avoids broken IPv6 routes."""
import sys
import pip._vendor.urllib3.util.connection as connection
from pip._internal.cli.main import main

connection.HAS_IPV6 = False
raise SystemExit(main(["install", "--only-binary=:all:", "--timeout", "30", "--retries", "2", "-r", sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"]))
