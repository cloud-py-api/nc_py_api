"""Example of using Recommendations API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Recommendations API is available
if nc.recommendations.available:
    # Get recommendations (limit to 10)
    recommendations = nc.recommendations.get_recommendations(limit=10)

    print(f"Found {len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"  - {rec.file_name} (path: {rec.file_path}, score: {rec.score})")
        if rec.reason:
            print(f"    Reason: {rec.reason}")

    # Get recommendation settings
    settings = nc.recommendations.get_settings()
    print(f"\nRecommendation settings: {settings}")
else:
    print("Recommendations API is not available on this Nextcloud instance.")
