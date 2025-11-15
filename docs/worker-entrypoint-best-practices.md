# Worker Entrypoint Best Practices

## Overview

When you start your app with `uv run agent.py dev`, it registers as a **worker** with the LiveKit server. The server manages dispatching programmatic participants to rooms by sending requests to available workers.

A [programmatic participant](https://docs.livekit.io/agents/worker/#programmatic-participants) is any code that joins a LiveKit room as a participant—this includes AI agents, media processors, or custom logic that processes realtime streams. This topic describes the worker lifecycle for AI agents, but the same lifecycle applies to all programmatic participants.

## Lifecycle

When a user connects to a [room](https://docs.livekit.io/home/get-started/api-primitives/#room), a worker fulfills the request to dispatch an agent to the room. An overview of the worker lifecycle is as follows:

1. **Worker registration**: Your agent code registers itself as a "worker" with LiveKit server, then waits on standby for requests.
2. **Job request**: When a user connects to a room, LiveKit server sends a request to an available worker. A worker accepts and starts a new process to handle the job. This is also known as [agent dispatch](https://docs.livekit.io/agents/worker/agent-dispatch/).
3. **Job**: The job initiated by your `entrypoint` function. This is the bulk of the code and logic you write. To learn more, see [Job lifecycle](https://docs.livekit.io/agents/worker/job/).
4. **LiveKit session close**: By default, a room is automatically closed when the last non-agent participant leaves. Any remaining agents disconnect. You can also [end the session](https://docs.livekit.io/agents/worker/job/#ending-the-session) manually.

Some additional features of workers include the following:

- Workers automatically exchange availability and capacity information with the LiveKit server, enabling load balancing of incoming requests.
- Each worker can run multiple jobs simultaneously, running each in its own process for isolation. If one crashes, it won't affect others running on the same worker.
- When you deploy updates, workers gracefully drain active LiveKit sessions before shutting down, ensuring sessions aren't interrupted.

## WorkerOptions Parameters

The interface for creating a worker is through the `WorkerOptions` class. The following only includes some of the available parameters. For the complete list, see the [WorkerOptions reference](https://docs.livekit.io/reference/python/v1/livekit/agents/index.html#livekit.agents.WorkerOptions).

**Use the quickstart first**

You can edit the agent created in the [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/) to try out the code samples in this topic.

**Python:**
```python
opts = WorkerOptions(
    # entrypoint function is called when a job is assigned to this worker
    # this is the only required parameter to WorkerOptions
    # https://docs.livekit.io/agents/worker/job/#entrypoint
    entrypoint_fnc,
    # inspect the request and decide if the current worker should handle it.
    request_fnc,
    # a function to perform any necessary initialization in a new process.
    prewarm_fnc,
    # whether the agent can subscribe to tracks, publish data, update metadata, etc.
    permissions,
    # amount of time to wait for existing jobs to finish when SIGTERM or SIGINT is received
    drain_timeout,
    # the type of worker to create, either JT_ROOM or JT_PUBLISHER
    worker_type=WorkerType.ROOM,
    # a function that reports the current system load, whether CPU or RAM, etc.
    load_fnc,
    # the maximum value of load_fnc, above which no new processes will spawn
    load_threshold,
    # set the agent name to enable explicit dispatch.
    # https://docs.livekit.io/agents/worker/agent-dispatch/
    agent_name,
)

# start the worker
cli.run_app(opts)
```

**Node.js:**
```typescript
const opts = new WorkerOptions({
  // path to a file that has {@link Agent} as a default export, dynamically imported later for
  // entrypoint and prewarm functions.
  agent,
  // inspect the request and decide if the current worker should handle it.
  requestFunc,
  // whether the agent can subscribe to tracks, publish data, update metadata, etc.
  permissions,
  // the type of worker to create, either JT_ROOM or JT_PUBLISHER
  workerType=JobType.JT_ROOM,
  // a function that reports the current load of the worker. returns a value between 0-1.
  loadFunc,
  // the maximum value of loadFunc, above which worker is marked as unavailable.
  loadThreshold,
  // set the agent name to enable explicit dispatch.
  // https://docs.livekit.io/agents/worker/agent-dispatch/
  agentName,
})

// Start the worker
cli.runApp(opts);
```

**Caution**

For security purposes, set the LiveKit API key and secret as environment variables rather than as `WorkerOptions` parameters.

## Entrypoint

The entrypoint function is the main function called for each new job, and is the heart of your agent app. To learn more, see the [entrypoint documentation](https://docs.livekit.io/agents/worker/job/#entrypoint) in the job lifecycle article.

**Python:**
```python
async def entrypoint(ctx: JobContext):
    # connect to the room
    # handle the session
    ...
```

**Node.js:**

In Node.js, the entrypoint function is defined as a property of the default export of the agent file:

```typescript
export default defineAgent({
  entry: async (ctx: JobContext) => {
    // connect to the room
    await ctx.connect();
    // handle the session
  },
});
```

## Request Handler

The `request_fnc` function runs each time the server has a job for the agent. The framework expects workers to explicitly accept or reject each job request. If the worker accepts the request, your entrypoint function is called. If the request is rejected, it's sent to the next available worker. A rejection indicates that the worker is unable to handle the job, not that the job itself is invalid. The framework simply reassigns it to another worker.

If `request_fnc` is not defined, the default behavior is to automatically accept all requests dispatched to the worker.

**Python:**
```python
async def request_fnc(req: JobRequest):
    # accept the job request
    await req.accept(
        # the agent's name (Participant.name), defaults to ""
        name="agent",
        # the agent's identity (Participant.identity), defaults to "agent-<jobid>"
        identity="identity",
        # attributes to set on the agent participant upon join
        attributes={"myagent": "rocks"},
    )

    # or reject it
    # await req.reject()

opts = WorkerOptions(entrypoint_fnc=entrypoint, request_fnc=request_fnc)
```

**Node.js:**
```typescript
const requestFunc = async (req: JobRequest) => {
  // accept the job request
  await req.accept(
    // the agent's name (Participant.name), defaults to ""
    'agent',
    // the agent's identity (Participant.identity), defaults to "agent-<jobid>"
    'identity',
  );
};

const opts = new WorkerOptions({
  // agent: ...
  requestFunc,
});
```

**Agent display name**

The `name` parameter is the display name of the agent, used to identify the agent in the room. It defaults to the agent's identity. This parameter is _not_ the same as the `agent_name` parameter for `WorkerOptions`, which is used to [explicitly dispatch](https://docs.livekit.io/agents/worker/agent-dispatch/) the agent to a room.

## Prewarm Function

For isolation and performance reasons, the framework runs each agent job in its own process. Agents often need access to model files that take time to load. To address this, you can use a `prewarm` function to warm up the process before assigning any jobs to it. You can control the number of processes to keep warm using the `num_idle_processes` parameter.

**Python:**
```python
def prewarm_fnc(proc: JobProcess):
    # load silero weights and store to process userdata
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # access the loaded silero instance
    vad: silero.VAD = ctx.proc.userdata["vad"]

opts = WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm_fnc)
```

**Node.js:**

In Node.js, the prewarm function is defined as a property of the default export of the agent file:

```typescript
export default defineAgent({
  prewarm: async (proc: JobProcess) => {
    // load silero weights and store to process userdata
    proc.userData.vad = await silero.VAD.load();
  },
  entry: async (ctx: JobContext) => {
    // access the loaded silero instance
    const vad = ctx.proc.userData.vad! as silero.VAD;
  },
});
```

## Worker Load

In [custom deployments](https://docs.livekit.io/agents/ops/deployment/custom/), you can configure the conditions under which the worker stops accepting new jobs through the `load_fnc` and `load_threshold` parameters.

- `load_fnc`: A function that returns the current load of the worker as a float between 0 and 1.0.
- `load_threshold`: The maximum load value at which the worker still accepts new jobs.

The default `load_fnc` is the worker's average CPU utilization over a 5-second window. The default `load_threshold` is `0.7`.

The following example shows how to define a custom load function that limits the worker to 9 concurrent jobs, independent of CPU usage:

**Python:**
```python
from livekit.agents import Worker, WorkerOptions

def compute_load(worker: Worker) -> float:
    return min(len(worker.active_jobs) / 10, 1.0)

opts = WorkerOptions(
    load_fnc=compute_load,
    load_threshold=0.9,
)
```

**Node.js:**
```typescript
import { Worker, WorkerOptions } from '@livekit/agents';

const computeLoad = (worker: Worker): Promise<number> => {
  return Math.min(worker.activeJobs.length / 10, 1.0);
};

const opts = new WorkerOptions({
  // agent: ...
  loadFunc: computeLoad,
  loadThreshold: 0.9,
});
```

**Note**

The `load_fnc` and `load_threshold` parameters cannot be changed in LiveKit Cloud deployments.

## Drain Timeout

Since agent sessions are stateful, they should not be terminated abruptly when the process is shutting down. The Agents framework supports graceful termination: when a `SIGTERM` or `SIGINT` is received, the worker enters a `draining` state. In this state, it stops accepting new jobs but allows existing ones to complete, up to a configured timeout.

The `drain_timeout` parameter sets the maximum time to wait for active jobs to finish. It defaults to 30 minutes.

## Permissions

By default, agents can both publish to and subscribe from the other participants in the same room. However, you can customize these permissions by setting the `permissions` parameter in `WorkerOptions`. To see the full list of parameters, see the [WorkerPermissions reference](https://docs.livekit.io/reference/python/v1/livekit/agents/index.html#livekit.agents.WorkerPermissions).

**Python:**
```python
opts = WorkerOptions(
    ...
    permissions=WorkerPermissions(
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        # when set to true, the agent won't be visible to others in the room.
        # when hidden, it will also not be able to publish tracks to the room as it won't be visible.
        hidden=False,
    ),
)
```

**Node.js:**
```typescript
const opts = new WorkerOptions({
  // agent: ...
  permissions: new WorkerPermissions({
    canPublish: true,
    canSubscribe: true,
    // when set to true, the agent won't be visible to others in the room.
    // when hidden, it will also not be able to publish tracks to the room as it won't be visible
    hidden: false,
  }),
});
```

## Worker Type

You can choose to start a new instance of the agent for each room or for each publisher in the room. This can be set when you register your worker:

**Python:**
```python
opts = WorkerOptions(
    ...
    # when omitted, the default is WorkerType.ROOM
    worker_type=WorkerType.ROOM,
)
```

**Node.js:**
```typescript
const opts = new WorkerOptions({
  // agent: ...
  // when omitted, the default is JobType.JT_ROOM
  workerType: JobType.JT_ROOM,
});
```

The `WorkerType` enum has two options:

- `ROOM`: Create a new instance of the agent for each room.
- `PUBLISHER`: Create a new instance of the agent for each publisher in the room.

If the agent is performing resource-intensive operations in a room that could potentially include multiple publishers (for example, processing incoming video from a set of security cameras), you can set `worker_type` to `JT_PUBLISHER` to ensure that each publisher has its own instance of the agent.

For `PUBLISHER` jobs, call the `entrypoint` function once for each publisher in the room. The `JobContext.publisher` object contains a `RemoteParticipant` representing that publisher.

## Starting the Worker

To spin up a worker with the configuration defined using `WorkerOptions`, call the CLI:

**Python:**
```python
if __name__ == "__main__":
    cli.run_app(opts)
```

**Node.js:**
```typescript
cli.runApp(opts);
```

The Agents worker CLI provides two subcommands: `start` and `dev`. The former outputs raw JSON data to stdout, and is recommended for production. `dev` is recommended to use for development, as it outputs human-friendly colored logs, and supports hot reloading on Python.

## Log Levels

By default, your worker and all of its job processes output logs at the `INFO` level or above. You can configure this behavior with the `--log-level` flag.

**Python:**
```shell
uv run agent.py start --log-level=DEBUG
```

**Node.js:**

**Run script must be set up in package.json**

The `start` script must be set up in your `package.json` file to run the following command. If you haven't already, see [Agent CLI modes](https://docs.livekit.io/agents/start/voice-ai/#cli-modes) for the command to add it.

```shell
pnpm run start --log-level=debug
```

The following log levels are available:

- `DEBUG`: Detailed information for debugging.
- `INFO`: Default level for general information.
- `WARNING`: Warning messages.
- `ERROR`: Error messages.
- `CRITICAL`: Critical error messages.

## Additional Resources

- [Worker lifecycle](https://docs.livekit.io/agents/worker/) - Overview of worker lifecycle
- [Job lifecycle](https://docs.livekit.io/agents/worker/job/) - Detailed information about job lifecycle
- [Agent dispatch](https://docs.livekit.io/agents/worker/agent-dispatch/) - How agents are dispatched to rooms
- [WorkerOptions reference](https://docs.livekit.io/reference/python/v1/livekit/agents/index.html#livekit.agents.WorkerOptions) - Complete API reference

