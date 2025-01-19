document.addEventListener('DOMContentLoaded', () => {
    const templateItems = document.querySelectorAll('.template-item');
    const editorArea = document.getElementById('editor-area');

    // Добавление шаблона при клике
    templateItems.forEach(item => {
        item.addEventListener('click', () => {
            const type = item.dataset.type;
            addTemplateToEditor(type);
        });
    });

    // Функция добавления элемента в редактор
    function addTemplateToEditor(type) {
        const container = document.createElement('div');
        container.classList.add('question-container');
        container.dataset.type = type; // Добавляем информацию о типе шаблона

        switch (type) {
            case 'checkbox':
                container.innerHTML = `
                    <div class="question-form">
    <textarea class="question-text" placeholder="Вопрос с множественным выбором"></textarea>
    <div class="options">
        <div class="option">
            <input type="checkbox" disabled>
            <input type="text" placeholder="Вариант ответа">
            <label>
                <input type="checkbox" class="correct-answer"> Правильный ответ
            </label>
        </div>
    </div>
    <button class="add-option">Добавить вариант</button>
</div>

                `;
                break;
            case 'radiobox':
                container.innerHTML = `
                    <div class="question-form">
                    <textarea class="question-text" placeholder="Вопрос с одним вариантом ответа"></textarea>
                    <div class="options">
                        <div class="option">
                            <input type="radio" disabled>
                            <input type="text" placeholder="Вариант ответа">
                            <label>
                                <input type="radio" class="correct-answer"> Правильный ответ
                            </label>
                        </div>
                    </div>
                    <button class="add-option">Добавить вариант</button>
                </div>
                `;
                break;
            case 'gap-fill':
                container.innerHTML = `
                    <div class="question-form">
  <p>Пропущенные слова</p>
  <textarea placeholder="Введите текст с пропусками"></textarea>
</div>
                `;
                break;
            case 'text':
                container.innerHTML = `
                    <div class="question-form">
  <p>Открытый вопрос</p>
  <textarea placeholder="Введите вопрос"></textarea>
</div>
                `;
                break;
        }

        // Добавление новых опций для checkbox и radiobox
        if (type === 'checkbox' || type === 'radiobox') {
            container.querySelector('.add-option').addEventListener('click', (event) => {
                event.preventDefault();

                const optionsContainer = container.querySelector('.options');
                const newOption = document.createElement('div');
                newOption.classList.add('option');
                newOption.innerHTML = `
                    <input type="${type === 'checkbox' ? 'checkbox' : 'radio'}" disabled>
                    <input type="text" placeholder="Вариант ответа">
                `;
                optionsContainer.appendChild(newOption);
            });
        }

        editorArea.appendChild(container);
    }

    // Сохранение задания
   document.getElementById('save-task').addEventListener('click', () => {
    const taskData = [];
    const questions = document.querySelectorAll('.question-container');

    questions.forEach(question => {
        const questionText = question.querySelector('p')?.innerText || question.querySelector('.question-text')?.value || '';
        const options = [...question.querySelectorAll('.options .option')].map(option => {
            const optionText = option.querySelector('input[type="text"]').value;
            const correctAnswer = option.querySelector('.correct-answer').checked;
            return { optionText, correctAnswer };
        });
        const state = question.dataset.type || 'unknown';

        taskData.push({ questionText, options, state });
    });

    fetch('/save_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({taskData, course_id})
    })
    .then(response => response.json())
    .then(data => {
        alert('Задание сохранено');
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при сохранении задания');
    });
});

});
down = '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#5f6368"><path d="M446.67-800v513l-240-240L160-480l320 320 320-320-46.67-47-240 240v-513h-66.66Z"/></svg>';
up = '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#5f6368"><path d="M446.67-160v-513l-240 240L160-480l320-320 320 320-46.67 47-240-240v513h-66.66Z"/></svg>'
state = true;
document.getElementById('toggle-btn').addEventListener('click', function() {
    if (state){
        document.getElementById('toggle-btn').innerHTML = up;
        state = false;
    } else{
        document.getElementById('toggle-btn').innerHTML = down;
        state = true;
    }
    const templates = document.getElementById('templates');
    templates.classList.toggle('open');
});
