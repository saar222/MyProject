# Create the English version of all project files

# 1. First, let's create the base.html template for English LTR support
base_html_en = '''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Randomness Testing System{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS (LTR) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.3rem;
        }
        
        .main-container {
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.95);
        }
        
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            border: none;
            padding: 1.5rem;
        }
        
        .btn {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        
        .progress {
            border-radius: 10px;
            height: 30px;
            background: rgba(0,0,0,0.1);
        }
        
        .progress-bar {
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .toast {
            border-radius: 10px;
            border: none;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .result-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .generator-info {
            background: rgba(102, 126, 234, 0.1);
            border: 2px solid rgba(102, 126, 234, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .footer {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding: 2rem 0;
            margin-top: 3rem;
        }
        
        .status-text {
            font-weight: 600;
            margin-top: 0.5rem;
        }
        
        .comparison-table {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: rgba(102, 126, 234, 0.95); backdrop-filter: blur(10px);">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="bi bi-dice-6"></i> Random Testing System
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">
                            <i class="bi bi-house"></i> Generator
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/tests">
                            <i class="bi bi-graph-up"></i> Statistical Tests
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container main-container">
        {% block content %}{% endblock %}
    </div>

    <!-- Footer -->
    <footer class="footer text-center text-white">
        <div class="container">
            <div class="row">
                <div class="col-md-12">
                    <p class="mb-0">
                        <i class="bi bi-code-slash"></i> 
                        Random Number Generator Testing System - Advanced Statistical Analysis
                    </p>
                    <small class="text-white-50">
                        Supports Python, Java, Time-based, and Sound generators
                    </small>
                </div>
            </div>
        </div>
    </footer>

    <!-- Toast Container -->
    <div class="toast-container position-fixed top-0 end-0 p-3">
        <div id="liveToast" class="toast" role="alert">
            <div class="toast-header">
                <i class="bi bi-info-circle text-primary me-2"></i>
                <strong class="me-auto" id="toastTitle">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body" id="toastBody">
                Message content here
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JS -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>'''

# Save base.html
with open('templates/base_en.html', 'w', encoding='utf-8') as f:
    f.write(base_html_en)

print("✅ Created base_en.html - English LTR base template")