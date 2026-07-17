const addactivity = async (userid, title, description, status) => {
    try {

        const res = await fetch(`http://localhost:3000/client/clients/add-activity/${userid}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description, status })
        });
        if (!res.ok) {
            return { error: `Error: ${res.status} ${res.statusText}` };
        }
        const data = await res.json();
        console.log("Activity added:", data);
        return data;

    } catch (error) {
        return { error: error.message };
    }
}

const incrementInferenceCount = async (userid) => {
    try {
        const res = await fetch(`http://localhost:3000/client/clients/increment-inference/${userid}`, {
            method: 'POST',
        });
        if (!res.ok) {
            return { error: `Error: ${res.status} ${res.statusText}` };
        }
        const data = await res.json();
        return data;
    } catch (error) {
        return { error: error.message };
    }
}

const incrementContributionCount = async (userid) => {
    try {
        const res = await fetch(`http://localhost:3000/client/clients/increment-contribution/${userid}`, {
            method: 'POST',
        });
        if (!res.ok) {
            return { error: `Error: ${res.status} ${res.statusText}` };
        }
        const data = await res.json();
        return data;
    } catch (error) {
        return { error: error.message };
    }
}

const updateTotalDataRowsAndSize = async (userid, rowsAdded, dataSize) => {
    try {
        const res = await fetch(`http://localhost:3000/client/clients/update-data-rows-and-size/${userid}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ rowsAdded, dataSize })
        });
        if (!res.ok) {
            return { error: `Error: ${res.status} ${res.statusText}` };
        }
        const data = await res.json();
        return data;
    } catch (error) {
        return { error: error.message };
    }
}

const getClientData = async (userid) => {
    try {
        const res = await fetch(`http://localhost:3000/client/clients/${userid}`);
        if (!res.ok) {
            return { error: `Error: ${res.status} ${res.statusText}` };
        }
        const data = await res.json();
        return { success: true, client: data };
    } catch (error) {
        return { success: false, error: error.message};
    }
};

export {
    addactivity,
    incrementInferenceCount,
    incrementContributionCount,
    updateTotalDataRowsAndSize,
    getClientData
};