
const API_URL = "http://127.0.0.1:5000";

let attributionChart = null;
let roiChart = null;


// Format currency in Indian Rupees

function formatCurrency(amount) {

    return Number(amount).toLocaleString("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    });

}


// Format ROI

function formatROI(roi) {

    if (roi === null || roi === undefined) {
        return "N/A";
    }

    return Number(roi).toFixed(2) + "%";

}


// Load Dashboard Summary

async function loadSummary() {

    try {

        const response = await fetch(`${API_URL}/api/summary`);

        if (!response.ok) {
            throw new Error("Unable to load summary");
        }

        const data = await response.json();

        document.getElementById("totalSpend").textContent =
            formatCurrency(data.total_spend);

        document.getElementById("totalRevenue").textContent =
            formatCurrency(data.total_revenue);

        document.getElementById("overallROI").textContent =
            formatROI(data.overall_roi);

    }

    catch (error) {

        console.error("Summary error:", error);

        document.getElementById("totalSpend").textContent = "Error";
        document.getElementById("totalRevenue").textContent = "Error";
        document.getElementById("overallROI").textContent = "Error";

    }

}


// Load Campaign Data

async function loadCampaigns() {

    const table = document.getElementById("campaignTable");

    try {

        const response = await fetch(`${API_URL}/api/campaigns`);

        if (!response.ok) {
            throw new Error("Unable to load campaigns");
        }

        const campaigns = await response.json();

        displayCampaigns(campaigns);

        createAttributionChart(campaigns);

        createROIChart(campaigns);

    }

    catch (error) {

        console.error("Campaign error:", error);

        table.innerHTML =
            '<tr><td colspan="5">Unable to load campaign data.</td></tr>';

    }

}


// Display Campaign Performance Table

function displayCampaigns(campaigns) {

    const table = document.getElementById("campaignTable");

    table.innerHTML = "";

    if (campaigns.length === 0) {

        table.innerHTML =
            '<tr><td colspan="5">No campaigns found.</td></tr>';

        return;

    }

    campaigns.forEach(campaign => {

        const row = document.createElement("tr");

        const values = [

            campaign.campaign_name,

            formatCurrency(campaign.total_spend),

            formatROI(campaign.first_touch_roi),

            formatROI(campaign.last_touch_roi),

            formatROI(campaign.linear_roi)

        ];

        values.forEach(value => {

            const cell = document.createElement("td");

            cell.textContent = value;

            row.appendChild(cell);

        });

        table.appendChild(row);

    });

}


// Campaign-wise Attribution Revenue Chart

function createAttributionChart(campaigns) {

    const ctx = document.getElementById("attributionChart");

    if (attributionChart) {

        attributionChart.destroy();

    }

    attributionChart = new Chart(ctx, {

        type: "bar",

        data: {

            labels: campaigns.map(campaign => campaign.campaign_id),

            datasets: [

                {
                    label: "First Touch Revenue",

                    data: campaigns.map(
                        campaign => campaign.first_touch_revenue
                    ),

                    backgroundColor: "#2563eb"
                },

                {
                    label: "Last Touch Revenue",

                    data: campaigns.map(
                        campaign => campaign.last_touch_revenue
                    ),

                    backgroundColor: "#16a34a"
                },

                {
                    label: "Linear Revenue",

                    data: campaigns.map(
                        campaign => campaign.linear_revenue
                    ),

                    backgroundColor: "#9333ea"
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                tooltip: {

                    callbacks: {

                        label: function(context) {

                            return context.dataset.label + ": " +
                                formatCurrency(context.raw);

                        }

                    }

                }

            },

            scales: {

                x: {

                    title: {

                        display: true,

                        text: "Campaign ID"

                    }

                },

                y: {

                    beginAtZero: true,

                    title: {

                        display: true,

                        text: "Attributed Revenue (INR)"

                    }

                }

            }

        }

    });

}


// Campaign-wise ROI Comparison Chart

function createROIChart(campaigns) {

    const ctx = document.getElementById("roiChart");

    if (roiChart) {

        roiChart.destroy();

    }

    roiChart = new Chart(ctx, {

        type: "bar",

        data: {

            labels: campaigns.map(campaign => campaign.campaign_id),

            datasets: [

                {

                    label: "First Touch ROI",

                    data: campaigns.map(
                        campaign => campaign.first_touch_roi
                    ),

                    backgroundColor: "#2563eb"

                },

                {

                    label: "Last Touch ROI",

                    data: campaigns.map(
                        campaign => campaign.last_touch_roi
                    ),

                    backgroundColor: "#16a34a"

                },

                {

                    label: "Linear ROI",

                    data: campaigns.map(
                        campaign => campaign.linear_roi
                    ),

                    backgroundColor: "#9333ea"

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                tooltip: {

                    callbacks: {

                        label: function(context) {

                            return context.dataset.label + ": " +
                                formatROI(context.raw);

                        }

                    }

                }

            },

            scales: {

                x: {

                    title: {

                        display: true,

                        text: "Campaign ID"

                    }

                },

                y: {

                    title: {

                        display: true,

                        text: "ROI Percentage"

                    }

                }

            }

        }

    });

}


// Initialize Dashboard

async function loadDashboard() {

    await loadSummary();

    await loadCampaigns();

}


// Start Dashboard

loadDashboard();
