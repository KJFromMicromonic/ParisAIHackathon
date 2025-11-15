"""CLI tool for generating LiveKit access tokens."""

import argparse
import sys

from app.core.security import generate_access_token


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Generate LiveKit access token")
    parser.add_argument("room_name", help="LiveKit room name")
    parser.add_argument("participant_identity", help="Participant identity")
    parser.add_argument(
        "--participant-name",
        help="Participant display name (optional)",
        default=None,
    )
    parser.add_argument(
        "--expires-in",
        type=int,
        help="Token expiration time in seconds (default: 3600)",
        default=3600,
    )

    args = parser.parse_args()

    try:
        token = generate_access_token(
            room_name=args.room_name,
            participant_identity=args.participant_identity,
            participant_name=args.participant_name,
            expires_in=args.expires_in,
        )

        print(token)
        sys.exit(0)

    except Exception as e:
        print(f"Error generating token: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

