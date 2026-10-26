const fetch = require('node-fetch');

module.exports = async (req, res) => {
    // Permite requisições do front-end
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ status: 'error', message: 'Método não permitido' });
    }

    const { service, link, quantity } = req.body || {};

    if (!service || !link || !quantity) {
        return res.status(400).json({ status: 'error', message: 'Preencha todos os campos.' });
    }

    const apiKey = '8decc58e80e51b08998f722e3aac36e8';
    const apiUrl = 'https://smmpainel.com/api/v2';

    try {
        const params = new URLSearchParams();
        params.append('key', apiKey);
        params.append('action', 'add');
        params.append('service', service);
        params.append('link', link);
        params.append('quantity', quantity);

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: params
        });

        const data = await response.json();

        if (data.order) {
            return res.status(200).json({
                status: 'success',
                message: 'Pedido realizado com sucesso!',
                order_id: data.order
            });
        } else {
            return res.status(400).json({
                status: 'error',
                message: 'Erro no provedor: ' + JSON.stringify(data)
            });
        }
    } catch (error) {
        return res.status(500).json({ status: 'error', message: 'Erro interno no servidor.' });
    }
};
