<?php
// Permite requisições do front-end
header('Content-Type: application/json');

// Inclui a classe da API que criamos acima
require_once 'Api.php';

// Pega os dados enviados pelo JavaScript do site
$input = json_decode(file_get_contents('php://input'), true);

$serviceId = $input['service'] ?? null;
$link      = $input['link'] ?? null;
$quantity  = $input['quantity'] ?? null;

// Valida se os campos preenchidos existem
if (!$serviceId || !$link || !$quantity) {
    echo json_encode(['status' => 'error', 'message' => 'Preencha todos os campos corretamente.']);
    exit;
}

// Inicia a API
$api = new Api();

// Dispara o pedido lá na smmpainel.com
$orderResponse = $api->order([
    'service'  => $serviceId,
    'link'     => $link,
    'quantity' => $quantity
]);

// Verifica se o pedido foi aceito com sucesso
if (isset($orderResponse->order)) {
    echo json_encode([
        'status' => 'success',
        'message' => 'Pedido realizado com sucesso!',
        'order_id' => $orderResponse->order
    ]);
} else {
    echo json_encode([
        'status' => 'error',
        'message' => 'Erro ao processar no provedor: ' . json_encode($orderResponse)
    ]);
}
?>
