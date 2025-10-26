const attendanceChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: dateLabels,
        datasets: [{
            label: 'Daily Attendance',
            data: attendanceData
        }]
    }
});