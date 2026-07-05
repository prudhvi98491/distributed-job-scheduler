document.addEventListener('DOMContentLoaded', () => {
    // API State
    let selectedJobId = null;

    // Elements
    const elements = {
        queuedVal: document.querySelector('#metric-queued .metric-value'),
        runningVal: document.querySelector('#metric-running .metric-value'),
        completedVal: document.querySelector('#metric-completed .metric-value'),
        failedVal: document.querySelector('#metric-failed .metric-value'),
        dlqVal: document.querySelector('#metric-dlq .metric-value'),
        
        singleQueueSelect: document.querySelector('#single-queue'),
        batchQueueSelect: document.querySelector('#batch-queue'),
        flowQueueSelect: document.querySelector('#flow-queue'),
        cronQueueSelect: document.querySelector('#cron-queue'),
        
        queuesTableBody: document.querySelector('#queues-table tbody'),
        workersTableBody: document.querySelector('#workers-table tbody'),
        cronTableBody: document.querySelector('#cron-table tbody'),
        jobsTableBody: document.querySelector('#jobs-table tbody'),
        
        filterQueue: document.querySelector('#filter-queue'),
        filterStatus: document.querySelector('#filter-status'),
        btnRefresh: document.querySelector('#btn-refresh'),
        
        // Forms
        formSingle: document.querySelector('#form-single-job'),
        formBatch: document.querySelector('#form-batch-job'),
        formWorkflow: document.querySelector('#form-workflow-job'),
        formCron: document.querySelector('#form-cron-job'),
        
        // Drawer
        jobDrawer: document.querySelector('#job-drawer'),
        drawerClose: document.querySelector('#drawer-close-btn'),
        drawerTitle: document.querySelector('#drawer-title'),
        drawerId: document.querySelector('#drawer-id'),
        drawerStatus: document.querySelector('#drawer-status'),
        drawerQueue: document.querySelector('#drawer-queue'),
        drawerRetries: document.querySelector('#drawer-retries'),
        drawerWorker: document.querySelector('#drawer-worker'),
        drawerPayload: document.querySelector('#drawer-payload'),
        drawerErrorContainer: document.querySelector('#drawer-error-container'),
        drawerError: document.querySelector('#drawer-error'),
        drawerTimeline: document.querySelector('#drawer-timeline'),
        drawerActions: document.querySelector('#drawer-actions')
    };

    // Tab Switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });

    // Close Drawer
    elements.drawerClose.addEventListener('click', () => {
        elements.jobDrawer.classList.remove('active');
    });

    // Initial Fetch & Setup
    async function init() {
        await loadQueuesSelector();
        await pollData();
        
        // Start polling every 2 seconds
        setInterval(pollData, 2000);
    }

    // Load queues list to populate dropdown inputs
    async function loadQueuesSelector() {
        try {
            const res = await fetch('/api/queues');
            const queues = await res.json();
            
            // Clear existing options
            elements.singleQueueSelect.innerHTML = '';
            elements.batchQueueSelect.innerHTML = '';
            elements.flowQueueSelect.innerHTML = '';
            elements.cronQueueSelect.innerHTML = '';
            elements.filterQueue.innerHTML = '<option value="">All Queues</option>';
            
            queues.forEach(q => {
                const opt = `<option value="${q.name}">${q.name} (Priority: ${q.priority})</option>`;
                elements.singleQueueSelect.innerHTML += opt;
                elements.batchQueueSelect.innerHTML += opt;
                elements.flowQueueSelect.innerHTML += opt;
                elements.cronQueueSelect.innerHTML += opt;
                
                elements.filterQueue.innerHTML += `<option value="${q.id}">${q.name}</option>`;
            });
        } catch (e) {
            console.error("Error loading queues list:", e);
        }
    }

    // Main Polling function
    async function pollData() {
        await Promise.all([
            fetchMetrics(),
            fetchQueues(),
            fetchWorkers(),
            fetchCronJobs(),
            fetchJobs()
        ]);
    }

    // Fetch metric counts
    async function fetchMetrics() {
        try {
            const res = await fetch('/api/metrics');
            const data = await res.json();
            
            elements.queuedVal.textContent = data.jobs_summary.queued;
            elements.runningVal.textContent = data.jobs_summary.running;
            elements.completedVal.textContent = data.jobs_summary.completed;
            elements.failedVal.textContent = data.jobs_summary.failed;
            elements.dlqVal.textContent = data.jobs_summary.dlq;
        } catch (e) {
            console.error("Error fetching metrics:", e);
        }
    }

    // Fetch Queues
    async function fetchQueues() {
        try {
            const res = await fetch('/api/queues');
            const queues = await res.json();
            
            elements.queuesTableBody.innerHTML = '';
            for (const q of queues) {
                // Fetch stats for this queue
                const statsRes = await fetch(`/api/queues/${q.id}/stats`);
                const statsData = await statsRes.json();
                const stats = statsData.stats;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${q.name}</strong></td>
                    <td>${q.priority}</td>
                    <td>${q.concurrency_limit}</td>
                    <td>${q.retry_policy_id ? 'Active' : 'None'}</td>
                    <td>
                        <span class="badge ${q.is_paused ? 'badge-failed' : 'badge-completed'}">
                            ${q.is_paused ? 'PAUSED' : 'ACTIVE'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-secondary btn-xs toggle-queue-btn" data-id="${q.id}" data-paused="${q.is_paused}">
                            ${q.is_paused ? 'Resume' : 'Pause'}
                        </button>
                    </td>
                `;
                elements.queuesTableBody.appendChild(tr);
            }

            // Bind toggle listeners
            document.querySelectorAll('.toggle-queue-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const qId = btn.getAttribute('data-id');
                    const isPausedNow = btn.getAttribute('data-paused') === 'true';
                    await toggleQueue(qId, !isPausedNow);
                });
            });
        } catch (e) {
            console.error("Error fetching queues:", e);
        }
    }

    async function toggleQueue(queueId, pauseState) {
        try {
            await fetch(`/api/queues/${queueId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_paused: pauseState })
            });
            await fetchQueues();
        } catch (e) {
            console.error("Failed to toggle queue state:", e);
        }
    }

    // Fetch Workers
    async function fetchWorkers() {
        try {
            const res = await fetch('/api/workers');
            const workers = await res.json();
            
            elements.workersTableBody.innerHTML = '';
            if (workers.length === 0) {
                elements.workersTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:gray;">No workers registered</td></tr>';
                return;
            }
            
            workers.forEach(w => {
                const tr = document.createElement('tr');
                const lastPulse = new Date(w.last_heartbeat_at).toLocaleTimeString();
                
                tr.innerHTML = `
                    <td>${w.id}</td>
                    <td><span class="badge badge-${w.status}">${w.status}</span></td>
                    <td>${w.active_jobs_count} / ${w.concurrency_limit}</td>
                    <td>${lastPulse}</td>
                `;
                elements.workersTableBody.appendChild(tr);
            });
        } catch (e) {
            console.error("Error fetching workers:", e);
        }
    }

    // Fetch Cron Jobs
    async function fetchCronJobs() {
        try {
            const res = await fetch('/api/jobs/cron/list');
            const crons = await res.json();
            
            elements.cronTableBody.innerHTML = '';
            if (crons.length === 0) {
                elements.cronTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:gray;">No cron schedules</td></tr>';
                return;
            }
            
            crons.forEach(c => {
                const tr = document.createElement('tr');
                const nextRun = c.next_run_at ? new Date(c.next_run_at).toLocaleTimeString() : '-';
                
                tr.innerHTML = `
                    <td><strong>${c.name}</strong></td>
                    <td><code>${c.cron_expression}</code></td>
                    <td>${nextRun}</td>
                    <td>
                        <button class="btn btn-secondary btn-xs toggle-cron-btn" data-id="${c.id}">
                            ${c.is_active ? 'Disable' : 'Enable'}
                        </button>
                    </td>
                `;
                elements.cronTableBody.appendChild(tr);
            });

            // Bind toggle listeners
            document.querySelectorAll('.toggle-cron-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const cronId = btn.getAttribute('data-id');
                    await toggleCron(cronId);
                });
            });
        } catch (e) {
            console.error("Error fetching cron jobs:", e);
        }
    }

    async function toggleCron(cronId) {
        try {
            await fetch(`/api/jobs/cron/${cronId}/toggle`, { method: 'POST' });
            await fetchCronJobs();
        } catch (e) {
            console.error("Failed to toggle cron job:", e);
        }
    }

    // Fetch Jobs List
    async function fetchJobs() {
        try {
            const qId = elements.filterQueue.value;
            const status = elements.filterStatus.value;
            
            let url = `/api/jobs?limit=25`;
            if (qId) url += `&queue_id=${qId}`;
            if (status) url += `&status_filter=${status}`;
            
            const res = await fetch(url);
            const data = await res.json();
            
            elements.jobsTableBody.innerHTML = '';
            if (data.jobs.length === 0) {
                elements.jobsTableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:gray;">No jobs found</td></tr>';
                return;
            }
            
            data.jobs.forEach(j => {
                const tr = document.createElement('tr');
                tr.style.cursor = 'pointer';
                tr.addEventListener('click', () => openJobDrawer(j.id));
                
                const createdTime = new Date(j.created_at).toLocaleTimeString();
                const scheduledTime = new Date(j.scheduled_at).toLocaleTimeString();
                
                tr.innerHTML = `
                    <td><code style="color:#a5b4fc">${j.id.substring(0, 8)}...</code></td>
                    <td><strong>${j.name}</strong></td>
                    <td>${j.queue_id}</td>
                    <td>${j.priority_override}</td>
                    <td><span class="badge badge-${j.status}">${j.status}</span></td>
                    <td>${createdTime}</td>
                    <td>${scheduledTime}</td>
                    <td>
                        <button class="btn btn-secondary btn-xs inspect-job-btn" data-id="${j.id}">Inspect</button>
                    </td>
                `;
                elements.jobsTableBody.appendChild(tr);
            });
        } catch (e) {
            console.error("Error fetching jobs:", e);
        }
    }

    // Inspect job details & open Drawer
    async function openJobDrawer(jobId) {
        try {
            selectedJobId = jobId;
            const res = await fetch(`/api/jobs/${jobId}`);
            if (res.status === 404) return;
            const data = await res.json();
            const job = data.job;
            const executions = data.executions;
            
            // Populate basic details
            elements.drawerTitle.textContent = job.name;
            elements.drawerId.textContent = `Job ID: ${job.id}`;
            elements.drawerStatus.className = `badge badge-${job.status}`;
            elements.drawerStatus.textContent = job.status;
            elements.drawerQueue.textContent = job.queue_id;
            elements.drawerRetries.textContent = `${job.retry_count} / ${job.max_retries}`;
            elements.drawerWorker.textContent = job.worker_id || 'None';
            elements.drawerPayload.textContent = JSON.stringify(JSON.parse(job.payload || '{}'), null, 2);
            
            // Show error message if it failed
            if (job.error_message) {
                elements.drawerErrorContainer.style.display = 'block';
                elements.drawerError.textContent = job.error_message;
            } else {
                elements.drawerErrorContainer.style.display = 'none';
            }
            
            // Populate timeline attempts
            elements.drawerTimeline.innerHTML = '';
            if (executions.length === 0) {
                elements.drawerTimeline.innerHTML = '<p style="color:gray; font-size:12px;">No executions logged yet.</p>';
            } else {
                executions.forEach((ex, index) => {
                    const div = document.createElement('div');
                    const statusClass = ex.status === 'completed' ? 'success' : (ex.status === 'failed' ? 'failed' : 'running');
                    const dur = ex.duration_ms ? `${ex.duration_ms}ms` : 'Running...';
                    const time = new Date(ex.started_at).toLocaleString();
                    
                    div.className = `timeline-item ${statusClass}`;
                    div.innerHTML = `
                        <div class="timeline-header">
                            <span>Attempt #${executions.length - index} (${ex.status})</span>
                            <span>${dur}</span>
                        </div>
                        <div class="timeline-detail">Started at: ${time}</div>
                        ${ex.error_message ? `<div class="timeline-detail" style="color:#f87171; margin-top:4px;">Error: ${ex.error_message.split('\n')[0]}</div>` : ''}
                    `;
                    elements.drawerTimeline.appendChild(div);
                });
            }
            
            // Setup actions (like manual retry button)
            elements.drawerActions.innerHTML = '';
            if (job.status === 'failed' || job.status === 'dlq') {
                const btn = document.createElement('button');
                btn.className = 'btn btn-primary';
                btn.textContent = 'Retry Job Manually';
                btn.addEventListener('click', async () => {
                    btn.disabled = true;
                    btn.textContent = 'Retrying...';
                    await retryJob(job.id);
                });
                elements.drawerActions.appendChild(btn);
            }
            
            elements.jobDrawer.classList.add('active');
        } catch (e) {
            console.error("Error inspecting job details:", e);
        }
    }

    async function retryJob(jobId) {
        try {
            await fetch(`/api/jobs/${jobId}/retry`, { method: 'POST' });
            elements.jobDrawer.classList.remove('active');
            await pollData();
        } catch (e) {
            console.error("Failed to retry job:", e);
        }
    }

    // Submit Handlers
    // 1. Single / Delayed Job
    elements.formSingle.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payloadStr = document.querySelector('#single-payload').value;
        let payload = {};
        try {
            payload = JSON.parse(payloadStr);
        } catch (err) {
            alert("Invalid JSON format in payload field");
            return;
        }

        const data = {
            queue_name: elements.singleQueueSelect.value,
            name: document.querySelector('#single-type').value,
            payload: payload,
            priority_override: parseInt(document.querySelector('#single-priority').value),
            delay_seconds: parseInt(document.querySelector('#single-delay').value) || null
        };

        try {
            const res = await fetch('/api/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                elements.formSingle.reset();
                document.querySelector('#single-payload').value = '{"duration": 3, "should_fail": false}';
                await pollData();
            } else {
                const error = await res.json();
                alert(`Error enqueuing: ${error.detail}`);
            }
        } catch (e) {
            console.error("Failed to enqueue job:", e);
        }
    });

    // 2. Batch Jobs Dispatch
    elements.formBatch.addEventListener('submit', async (e) => {
        e.preventDefault();
        const count = parseInt(document.querySelector('#batch-count').value);
        const name = document.querySelector('#batch-name').value;
        const queue = elements.batchQueueSelect.value;
        
        // Generate list of simple job payloads
        const jobs = [];
        for (let i = 0; i < count; i++) {
            jobs.push({ item_index: i, duration: 2, batch_id: name });
        }

        const data = {
            queue_name: queue,
            name: name,
            jobs: jobs,
            priority_override: 0
        };

        try {
            const res = await fetch('/api/jobs/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                await pollData();
            } else {
                const error = await res.json();
                alert(`Error dispatching batch: ${error.detail}`);
            }
        } catch (e) {
            console.error(e);
        }
    });

    // 3. Workflow Pipelines (Parent & Dependent Child sequential submission)
    elements.formWorkflow.addEventListener('submit', async (e) => {
        e.preventDefault();
        const qName = elements.flowQueueSelect.value;
        const pName = document.querySelector('#flow-parent-name').value;
        const cName = document.querySelector('#flow-child-name').value;
        const failParent = document.querySelector('#flow-fail-parent').value === 'true';

        try {
            // A. Dispatch Parent Job first
            const parentRes = await fetch('/api/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    queue_name: qName,
                    name: pName,
                    payload: { duration: 4, should_fail: failParent, error_msg: "Simulated workflow parent failure" },
                    priority_override: 0
                })
            });
            
            if (!parentRes.ok) {
                const err = await parentRes.json();
                alert(`Failed to create parent job: ${err.detail}`);
                return;
            }
            
            const parentJob = await parentRes.json();
            
            // B. Dispatch Child Job dependent on Parent Job ID
            const childRes = await fetch('/api/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    queue_name: qName,
                    name: cName,
                    payload: { duration: 2 },
                    priority_override: 0,
                    parent_job_id: parentJob.id
                })
            });

            if (childRes.ok) {
                alert(`Workflow pipeline dispatched!\n\nParent Job ID: ${parentJob.id.substring(0,8)}... (Active)\nChild Job: Blocked until Parent finishes.`);
                await pollData();
            } else {
                const err = await childRes.json();
                alert(`Failed to create dependent child: ${err.detail}`);
            }
        } catch (err) {
            console.error(err);
        }
    });

    // 4. Cron Registration
    elements.formCron.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let payload = null;
        const payloadVal = document.querySelector('#cron-payload').value;
        if (payloadVal) {
            try {
                payload = JSON.parse(payloadVal);
            } catch (err) {
                alert("Invalid cron payload JSON format");
                return;
            }
        }

        const data = {
            queue_name: elements.cronQueueSelect.value,
            name: document.querySelector('#cron-name').value,
            cron_expression: document.querySelector('#cron-expr').value,
            payload: payload
        };

        try {
            const res = await fetch('/api/jobs/cron', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                elements.formCron.reset();
                document.querySelector('#cron-expr').value = '*/10 * * * * *';
                document.querySelector('#cron-payload').value = '{"duration": 1}';
                await pollData();
            } else {
                const error = await res.json();
                alert(`Error creating cron: ${error.detail}`);
            }
        } catch (e) {
            console.error(e);
        }
    });

    // Filters and manual refresh actions
    elements.filterQueue.addEventListener('change', fetchJobs);
    elements.filterStatus.addEventListener('change', fetchJobs);
    elements.btnRefresh.addEventListener('click', fetchJobs);

    // Initialize Dashboard Application
    init();
});
