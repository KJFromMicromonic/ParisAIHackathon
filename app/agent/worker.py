"""LiveKit agent worker entrypoint."""

from livekit import agents
from livekit.agents import JobContext, WorkerOptions
from livekit.agents.log import logger

from app.agent.session import AgentSessionManager


async def entrypoint(ctx: JobContext) -> None:
    """
    Agent entrypoint function called for each new job.

    This function is called when a user connects to a room and the agent
    is dispatched to handle the session.

    Args:
        ctx: Job context containing room and connection information
    """
    logger.info(
        "Agent entrypoint called",
        extra={
            "room_name": ctx.room.name,
            "job_id": ctx.job.id,
        },
    )

    try:
        # Connect to the room
        await ctx.connect()

        logger.info(
            "Connected to room",
            extra={"room_name": ctx.room.name},
        )

        # Create and start session manager
        session_manager = AgentSessionManager(ctx.room)

        try:
            await session_manager.start()

            # Wait for room to disconnect
            # Use asyncio.Event to wait for the disconnected event
            import asyncio
            disconnected = asyncio.Event()

            def on_disconnected(*args):
                disconnected.set()

            ctx.room.on("disconnected", on_disconnected)
            
            # Wait for disconnection
            await disconnected.wait()

        finally:
            # Clean up session manager
            await session_manager.stop()

        logger.info(
            "Agent session ended",
            extra={"room_name": ctx.room.name},
        )

    except Exception as e:
        logger.error(
            f"Error in agent entrypoint: {e}",
            exc_info=True,
            extra={"room_name": ctx.room.name},
        )
        raise


async def request_fnc(req: agents.JobRequest) -> None:
    """
    Request handler function called when a job is assigned to this worker.

    This function can inspect the request and decide whether to accept or reject it.
    By default, we accept all requests.

    Args:
        req: Job request containing room and participant information
    """
    # Accept the job request
    # Note: If identity is not provided, req.accept() will auto-generate "agent-{req.id}"
    await req.accept(
        name="visually-impaired-assistant",
        identity=f"agent-{req.id}",
        attributes={
            "agent_type": "visually-impaired-assistant",
            "capabilities": "video_obstacle_detection,voice_assistant,mcp_tools",
        },
    )

    logger.info(
        "Accepted job request",
        extra={
            "job_id": req.id,
            "room_name": req.room.name,
        },
    )


def main() -> None:
    """Main function to start the agent worker."""
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_fnc,
        worker_type=agents.WorkerType.ROOM,
    )

    agents.cli.run_app(opts)


if __name__ == "__main__":
    main()

