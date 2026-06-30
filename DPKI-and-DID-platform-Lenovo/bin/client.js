const net = require('net');
const path = require('path');
const fs = require('fs');

const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;


function createClientConnection(PORT, HOST) {
    const client = new net.Socket();
    client.connect(PORT, HOST, () => {
        console.log('Connected to server');
    });
    return client;
}

function isJsonString(str) {
    try {
        JSON.parse(str);
        return true;
    } catch (e) {
        return false;
    }
}

function handleClientEvents(client) {
    client.on('data', (data) => {
        const response = data.toString();
        if (isJsonString(response)) {
            const jsonResponse = JSON.parse(response);
            const filePath = path.join(exeDir, '..', 'config', 'DPKI-config.json');
            fs.writeFileSync(filePath, JSON.stringify(jsonResponse, null, 2), 'utf8');
            console.log(`Configuration updated and saved to ${filePath}`);
            client.end();
        } else {
            console.log('Message received:', data.toString());
            client.end();
        }
    });

    client.on('end', () => {
        console.log('Server closed the connection');
    });

    client.on('close', () => {
        console.log('Connection closed by client');
    });

    client.on('error', (err) => {
        console.error('Connection error:', err.message);
    });
}

module.exports = { createClientConnection, handleClientEvents }