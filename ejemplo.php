<?php
// api.php - API REST segura en PHP

// 1. Aplicar Security Headers
header("X-Content-Type-Options: nosniff");
header("X-Frame-Options: DENY");
header("X-XSS-Protection: 1; mode=block");
header("Content-Security-Policy: default-src 'self'");
header("Content-Type: application/json; charset=utf-8");

// 2. CORS (solo tu frontend)
$allowed_origins = [
    'http://localhost:3000',
    'https://tu-frontend.com'
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins)) {
    header("Access-Control-Allow-Origin: $origin");
    header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE");
    header("Access-Control-Allow-Headers: Content-Type, Authorization");
}

// 3. Verificar tamaño del request (como en FastAPI)
$max_size = 1 * 1024 * 1024; // 1MB para JSON
$content_length = $_SERVER['CONTENT_LENGTH'] ?? 0;

if ($content_length > $max_size) {
    http_response_code(413);
    echo json_encode([
        'error' => 'Request body too large',
        'max_size_mb' => $max_size / 1024 / 1024
    ]);
    exit;
}

// 4. Rate Limiting simple
session_start();
$requests = $_SESSION['requests'] ?? 0;
$requests++;

if ($requests > 100) {
    http_response_code(429);
    echo json_encode(['error' => 'Too many requests']);
    exit;
}

$_SESSION['requests'] = $requests;

// 5. Tu API
$method = $_SERVER['REQUEST_METHOD'];
$input = json_decode(file_get_contents('php://input'), true);

switch($method) {
    case 'POST':
        // Validar entrada
        if (!isset($input['question'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Missing question']);
            exit;
        }
        
        // Sanitizar (prevenir XSS)
        $question = htmlspecialchars($input['question'], ENT_QUOTES, 'UTF-8');
        
        // Tu lógica aquí
        $answer = "Respuesta a: $question";
        
        echo json_encode([
            'question' => $question,
            'answer' => $answer
        ]);
        break;
        
    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
}
?>