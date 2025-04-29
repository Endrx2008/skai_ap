#include "mainwindow.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QScrollBar>
#include <QGuiApplication>
#include <QScreen>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent),
      chatDisplay(nullptr),
      inputLine(nullptr),
      sendButton(nullptr),
      ollamaProcess(nullptr)
{
    chatDisplay = new QTextEdit(this);
    inputLine = new QLineEdit(this);
    sendButton = new QPushButton("Send", this);
    ollamaProcess = new QProcess(this);

    setWindowTitle("Ollama Chat");

    // Set background gradient for the main window
    QPalette pal = palette();
    QLinearGradient gradient(0, 0, 0, height());
    gradient.setColorAt(0, QColor("#2c3e50"));
    gradient.setColorAt(1, QColor("#4ca1af"));
    pal.setBrush(QPalette::Window, QBrush(gradient));
    setAutoFillBackground(true);
    setPalette(pal);

    chatDisplay->setReadOnly(true);
    chatDisplay->setStyleSheet(
        "background-color: #1e1e1e; "
        "color: #d4d4d4; "
        "font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; "
        "font-size: 14px; "
        "border-radius: 10px; "
        "padding: 10px;"
    );

    inputLine->setPlaceholderText("Type your message here...");
    inputLine->setStyleSheet(
        "background-color: #252526; "
        "color: #d4d4d4; "
        "font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; "
        "font-size: 14px; "
        "border-radius: 10px; "
        "padding: 8px;"
    );

    sendButton->setStyleSheet(
        "background-color: #0e639c; "
        "color: white; "
        "font-weight: bold; "
        "border-radius: 10px; "
        "padding: 8px 16px;"
        "min-width: 80px;"
    );

    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(15, 15, 15, 15);
    mainLayout->setSpacing(10);
    mainLayout->addWidget(chatDisplay);

    QHBoxLayout *inputLayout = new QHBoxLayout();
    inputLayout->setSpacing(10);
    inputLayout->addWidget(inputLine);
    inputLayout->addWidget(sendButton);

    mainLayout->addLayout(inputLayout);

    connect(sendButton, &QPushButton::clicked, this, &MainWindow::onSendClicked);
    connect(inputLine, &QLineEdit::returnPressed, this, &MainWindow::onSendClicked);
    connect(ollamaProcess, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this, &MainWindow::onOllamaFinished);

    // Set window size to approx 5 cm width (189 pixels) and height 400 pixels
    resize(189, 400);

    // Position window at the right side of the primary screen
    QScreen *screen = QGuiApplication::primaryScreen();
    if (screen) {
        QRect screenGeometry = screen->geometry();
        int x = screenGeometry.x() + screenGeometry.width() - width() - 10; // 10 px margin from right edge
        int y = screenGeometry.y() + 50; // 50 px from top
        move(x, y);
    }

    // Enable window transparency and remove window background
    setAttribute(Qt::WA_TranslucentBackground);
    setWindowFlags(windowFlags() | Qt::FramelessWindowHint);
}

MainWindow::~MainWindow()
{
    if (ollamaProcess->state() == QProcess::Running) {
        ollamaProcess->kill();
        ollamaProcess->waitForFinished();
    }
}

void MainWindow::appendMessage(const QString &sender, const QString &message)
{
    QString color = (sender == "You") ? "#569CD6" : "#CE9178";
    chatDisplay->append(QString("<b><span style=\"color:%1;\">%2:</span></b> %3").arg(color, sender, message));
    QScrollBar *scrollBar = chatDisplay->verticalScrollBar();
    scrollBar->setValue(scrollBar->maximum());
}

void MainWindow::onSendClicked()
{
    QString userInput = inputLine->text().trimmed();
    if (userInput.isEmpty())
        return;

    appendMessage("You", userInput);
    inputLine->clear();

    // Call Ollama CLI with user input
    QString program = "ollama";
    QStringList arguments;
    arguments << "chat" << "llama2" << "--prompt" << userInput;

    ollamaProcess->start(program, arguments);
    sendButton->setEnabled(false);
    inputLine->setEnabled(false);
}

void MainWindow::onOllamaFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    Q_UNUSED(exitCode);
    Q_UNUSED(exitStatus);

    QByteArray output = ollamaProcess->readAllStandardOutput();
    QString response = QString::fromUtf8(output).trimmed();

    appendMessage("Ollama", response);

    sendButton->setEnabled(true);
    inputLine->setEnabled(true);
    inputLine->setFocus();
}
