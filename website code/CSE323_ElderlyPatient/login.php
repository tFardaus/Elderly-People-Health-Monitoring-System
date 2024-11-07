<?php
session_start();
$host = 'localhost';
$dbname = 'cse323';
$username = 'root';
$password = ''; // Default XAMPP password

$conn = new mysqli($host, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    $password = $_POST['password'];

    $stmt = $conn->prepare("SELECT * FROM doctors WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    $user = $result->fetch_assoc();

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['doctor_logged_in'] = true;
        echo "Login successful";
        header('Location: index.html');
        exit();
    } else {
        echo "Invalid credentials";
    }

    $stmt->close();
}
$conn->close();
?>
