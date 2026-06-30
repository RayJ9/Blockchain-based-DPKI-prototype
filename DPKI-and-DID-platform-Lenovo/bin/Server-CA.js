const net = require('net');
const path = require('path');
const fs = require('fs');

const PORT = 12349;
const HOST = '0.0.0.0';

const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;
const nodesDir = path.join(exeDir, '..', 'nodes');

const server = net.createServer((socket) => {
    console.log('New client connected:', socket.remoteAddress, socket.remotePort);
    socket.on('data', (data) => {
        console.log('Received message:', data.toString());
        try {
            const message = JSON.parse(data.toString());
            if (message.type === 'CSR') {
                const ueName = message.ue_name;
                const csrContent = message.csr_content;
                const csrDir1 = path.join(nodesDir, 'temp', `tempUE_${ueName}`);
                
                if (!fs.existsSync(csrDir1)) {
                    fs.mkdirSync(csrDir1, { recursive: true });
                }

                const csrDir2 = path.join(nodesDir, 'temp', `tempUE_${ueName}`, 'certs');
                if (!fs.existsSync(csrDir2)) {
                    fs.mkdirSync(csrDir2);
                }

                let config = {};
                configPath = path.join(exeDir, '..', 'config', 'DPKI-config.json')
                if (fs.existsSync(configPath)) {
                    try {
                        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                    } catch (err) {
                        console.error('Error reading config file:', err);
                    }
                }

                config[ueName] = {
                    "ueHost": socket.remoteAddress,
                    "uePort": 12348
                };

                fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
                console.log(`Config updated for ${ueName}`);

                const filePath = path.join(csrDir2, `${ueName}.csr`);
                fs.writeFile(filePath, csrContent, (err) => {
                    if (err) {
                        console.error('Store CSR failed:', err);
                        socket.write('Store CSR failed');
                    } else {
                        console.log(`CSR received:${filePath}`);
                        socket.write('CSR received, waiting for issue certificate');
                    }
                });
            }
            else if (message.type === 'updatelist') {
                const configPath = path.join(exeDir, '..', 'config', 'DPKI-config.json');
                const configData = fs.readFileSync(configPath, 'utf8');
                const configJson = JSON.parse(configData);
                socket.write(JSON.stringify(configJson, null, 2));

                
            } else {
                console.log('Unknown message type');
            }
        } catch (err) {
            console.error('Error processing message:', err);
        }
    });

    socket.on('end', () => {
        console.log('Client disconnected');
    });

    socket.on('error', (err) => {
        console.error('Socket error:', err.message);
    });
});

server.listen(PORT, HOST, () => {
    console.log(`Server listening on ${HOST}:${PORT}`);
});
