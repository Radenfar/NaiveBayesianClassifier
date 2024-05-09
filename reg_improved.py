class ImprovedNaiveBayes:
    def __init__(self, validation_data_split: float, alpha: float, stop_word_proportion: float, auto_load_data: bool = True) -> None:
        if auto_load_data:
            self.training_data: DataModel = DataModel(
                data_path=os.path.join(os.path.join("data", "trg.csv")),
                do_shuffle=True
            )
            self.testing_data: DataModel = DataModel(
                data_path=os.path.join(os.path.join("data", "tst.csv")),
                do_shuffle=False
            )
            self.training_data.eliminate_stop_words(stop_word_proportion)
            if validation_data_split > 0.0:
                self.validation_data: DataModel = self.training_data.split_model(validation_data_split)
            else:
                self.validation_data = None
            self.alpha = alpha
            self.vocab_size = self.training_data.vocabulary_size
            self.classes = [c for c in set([data.class_ for data in self.training_data.data])]
            self.class_counts = self.get_class_counts()
            self.class_probabilities = [count / len(self.training_data.data) for count in self.class_counts]
            self.word_counts = self.get_word_counts()
        else:
            self.training_data = DataModel('')
            self.testing_data = DataModel('')
            self.validation_data = None
            self.alpha = alpha
            self.vocab_size = 0
            self.classes = []
            self.class_counts = []
            self.class_probabilities = []
            self.word_counts = []


    def set_data(self, training_data: DataModel = None, testing_data: DataModel = None, validation_data: DataModel = None) -> None:
        if training_data:
            self.training_data.set_data(training_data.data)
        if testing_data:
            self.testing_data.set_data(testing_data.data)
        if validation_data:
            if self.validation_data:
                self.validation_data.set_data(validation_data.data)
            else:
                self.validation_data = DataModel('')
                self.validation_data.set_data(validation_data.data)
        self.vocab_size = self.training_data.vocabulary_size
        self.classes = [c for c in set([data.class_ for data in self.training_data.data])]
        if self.classes == []:
            print(f"Classes: {self.classes}")
            print(f"{self.training_data.data[0].class_}, {self.training_data.data[0].abstract}")
            print(f"{self.training_data.data[1].class_}, {self.training_data.data[1].abstract}")
        self.class_counts = self.get_class_counts()
        self.class_probabilities = [count / len(self.training_data.data) for count in self.class_counts]
        self.word_counts = self.get_word_counts()


    def get_validation_accuracy(self) -> float:
        if not self.validation_data:
            print(f"Model has no validation set.")
            return 0
        correct = 0
        for data in self.validation_data.data:
            predicted_class = self.classify_abstract(data.abstract)
            # print(f"Predicted: {predicted_class} | Actual: {data.class_}")
            if predicted_class == data.class_:
                correct += 1
        return correct / len(self.validation_data.data)


    def run_test_data(self, fileout: str, type_: str = "test") -> None:
        with open(fileout, 'w') as f:
            f.write("id,class\n")
            if type_ == "test":
                for data in self.testing_data.data:
                    f.write(f"{data.id},{self.classify_abstract(data.abstract)}\n")
            elif type_ == "train":
                for data in self.training_data.data:
                    f.write(f"{data.id},{self.classify_abstract(data.abstract)}\n")
            else:
                raise ValueError("Invalid type_ argument. Must be 'test', 'validation', or 'train'.")
    
    
    def get_word_probability(self, word: str, class_index: int) -> float:
        '''
        p(class|word) = p(word|class) * p(class) / p(word) -- NEW (Dirichlet)
        '''
        word_count = self.word_counts[class_index].get(word, 0)
        class_count = self.class_counts[class_index]
        word_in_class = (word_count + self.alpha) / (class_count + self.alpha * self.vocab_size)
        class_probability = self.class_probabilities[class_index]
        word_in_data = (sum([self.word_counts[i].get(word, 0) for i in range(len(self.classes))]) + self.alpha) / (len(self.training_data.data) + self.alpha * self.vocab_size)
        return word_in_class * class_probability / word_in_data


    def classify_abstract(self, abstract: str) -> str:
        '''Classifies the abstract into one of the classes. Returns the class. Uses the Naive Bayesian Classifier algorithm.'''
        abstract_words = abstract.split()

        # testing with mn words
        # abstract_words = self.training_data.split_abstract(abstract)
        abstract_words = abstract.split()

        class_probabilities = []
        for i in range(len(self.classes)):
            cur_class_probability = self.class_probabilities[i]
            cur_class_probability = 1
            for word in abstract_words:
                cur_word_probability = self.get_word_probability(word, i)
                if cur_word_probability == 0:
                    continue
                cur_class_probability *= cur_word_probability
            class_probabilities.append(cur_class_probability)
        max_class = self.classes[class_probabilities.index(max(class_probabilities))]
        return max_class
    


    def get_class_counts(self) -> list[int]:
        '''Returns the count of each class in the training data. Match the order of the classes with the order of self.classes (classes[i] -> class_counts[i])'''
        class_counts = [0] * len(self.classes)
        for data in self.training_data.data:
            class_counts[self.classes.index(data.class_)] += 1
        return class_counts
    

    def get_word_counts(self) -> list[dict[str, int]]:
        '''Returns the count of each word in each class. Match the order of the classes with the order of self.classes (classes[i] -> word_counts[i])'''
        word_counts = [{} for _ in range(len(self.classes))]
        for data in self.training_data.data:
            # testing with mn words
            # words = self.training_data.split_abstract(data.abstract)
            words = data.abstract.split()
            for word in words:
                if word not in word_counts[self.classes.index(data.class_)]:
                    word_counts[self.classes.index(data.class_)][word] = 1
                else:
                    word_counts[self.classes.index(data.class_)][word] += 1
        return word_counts
    

    def save(self):
        '''Saves the word counts to a txt file'''
        with open("word_counts.txt", 'w') as f:
            for i in range(len(self.classes)):
                f.write('-'*100 + '\n')
                f.write(f"Class: {self.classes[i]}\n")
                f.write(f"Class Count: {self.class_counts[i]}\n")
                f.write(f"Class Probability: {self.class_probabilities[i]}\n\n")
                for word, count in self.word_counts[i].items():
                    f.write(f"{word}: {count}\n")
