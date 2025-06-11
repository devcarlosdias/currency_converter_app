import 'package:bloc/bloc.dart';
import 'package:currency_converter_app/features/home/domain/usecases/get_supported_currency.dart';
import 'package:currency_converter_app/features/home/presentation/supported_event.dart';

class SupportedCubit extends Cubit<SupportedState> {
  SupportedCubit(this.usecase) : super(SupportedStart());

  final GetSupportedCurrency usecase;

  Future<void> getSupportedCurrency () async {
    emit(SupportedLoading());
      final result = await usecase();
      emit(result.fold((l) => SupportedError(), (r) => SupportedSuccess(r)));
  }
}

/* emit(SearchLoading());
      final result = await usecase(event.text);
      emit(result.fold((l) => SearchError(l), (r) => SearchSuccess(r))); */